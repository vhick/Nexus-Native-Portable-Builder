using System.Diagnostics;
using System.IO;
using System.Security.Principal;
using System.Text;
using System.Xml.Linq;
using System.Runtime.InteropServices;
using Nexus.Core.Logging;

namespace Nexus.App.Services;

/// <summary>
/// Optional, uniquely-owned elevated per-user Task Scheduler entry.
/// Never uses /F, never touches upstream's conventional "Nexus Optimizer" task.
/// The stable registration ID and last registered executable are stored under Data.
/// A moved folder requires explicit disable/re-enable; no silent repair.
/// </summary>
public sealed class AutostartService
{
    private readonly ActivityLog _log;
    private static readonly string StateDirectory = Path.Combine(AppContext.BaseDirectory, "Data", "Integrations");
    private static readonly string IdentityPath = Path.Combine(StateDirectory, "autostart-id.txt");
    private static readonly string RegisteredPath = Path.Combine(StateDirectory, "autostart-target.txt");
    private static readonly string XmlPath = Path.Combine(StateDirectory, "autostart-task.xml");
    public AutostartService(ActivityLog log) => _log = log;

    private static string TaskName
    {
        get
        {
            Directory.CreateDirectory(StateDirectory);
            if (!File.Exists(IdentityPath))
                File.WriteAllText(IdentityPath, Guid.NewGuid().ToString("N"), new UTF8Encoding(false));
            string id = File.ReadAllText(IdentityPath, Encoding.UTF8).Trim();
            if (id.Length != 32 || !Guid.TryParseExact(id, "N", out _))
                throw new InvalidDataException("Autostart ownership ID is corrupt; refusing to alter Windows tasks.");
            return "Nexus Native Portable-" + id;
        }
    }

    private static string? RegisteredTarget => File.Exists(RegisteredPath)
        ? File.ReadAllText(RegisteredPath, Encoding.UTF8).Trim() : null;

    private static string? ExistingTarget()
    {
        // Task Scheduler COM returns Unicode action paths without schtasks.exe console
        // code-page conversion. This is critical for portable paths with Unicode names.
        // COM is used to inspect ONLY; creation/deletion uses schtasks against an
        // already verified uniquely-owned task, never wildcard system task cleanup.
        Type schedulerType = Type.GetTypeFromProgID("Schedule.Service")
            ?? throw new InvalidOperationException("Task Scheduler COM API unavailable");
        object serviceObject = Activator.CreateInstance(schedulerType)
            ?? throw new InvalidOperationException("Cannot start Task Scheduler COM API");
        try
        {
            dynamic service = serviceObject;
            service.Connect();
            dynamic folder = service.GetFolder(@"\");
            dynamic task;
            try { task = folder.GetTask(TaskName); }
            catch (COMException ex) when (ex.HResult == unchecked((int)0x80070002) ||
                ex.HResult == unchecked((int)0x8004130F))
            {
                return null; // confirmed task not found (never mask Access Denied)
            }
            dynamic definition = task.Definition;
            string description = (string)definition.RegistrationInfo.Description;
            if (description != "Owned by Nexus Native Portable; exact task action checked before modification")
                return "__FOREIGN__";
            dynamic actions = definition.Actions;
            if ((int)actions.Count != 1) return "__FOREIGN__";
            dynamic action = actions.Item(1);
            if ((int)action.Type != 0) return "__FOREIGN__"; // TASK_ACTION_EXEC
            return (string)action.Path;
        }
        finally
        {
            Marshal.FinalReleaseComObject(serviceObject);
        }
    }

    private bool Owned(string? target)
    {
        if (target is null || target == "__FOREIGN__") return false;
        string? current = Environment.ProcessPath;
        string? recorded = RegisteredTarget;
        return (current is not null && string.Equals(target, current, StringComparison.OrdinalIgnoreCase))
            || (recorded is not null && string.Equals(target, recorded, StringComparison.OrdinalIgnoreCase));
    }

    public bool IsEnabled()
    {
        try { return Owned(ExistingTarget()); }
        catch (Exception ex) { _log.Warn("Autostart", "Cannot check owned task: " + ex.Message); return false; }
    }

    public bool SetEnabled(bool enabled)
    {
        try
        {
            string exe = Environment.ProcessPath ?? throw new InvalidOperationException("Cannot determine Nexus.exe path");
            string task = TaskName;
            string? existing = ExistingTarget();
            if (enabled)
            {
                if (existing is not null)
                {
                    if (string.Equals(existing, exe, StringComparison.OrdinalIgnoreCase) && Owned(existing)) return true;
                    _log.Warn("Autostart", "Existing task is foreign or uses a stale path. Disable the old owned task explicitly before re-enabling; never overwrite it.");
                    return false;
                }
                var ns = XNamespace.Get("http://schemas.microsoft.com/windows/2004/02/mit/task");
                string userSid = WindowsIdentity.GetCurrent().User?.Value ?? throw new InvalidOperationException("Windows SID unavailable");
                var doc = new XDocument(new XDeclaration("1.0", "UTF-16", null),
                    new XElement(ns + "Task", new XAttribute("version", "1.2"),
                        new XElement(ns + "RegistrationInfo", new XElement(ns + "Description",
                            "Owned by Nexus Native Portable; exact task action checked before modification")),
                        new XElement(ns + "Triggers", new XElement(ns + "LogonTrigger",
                            new XElement(ns + "Enabled", "true"), new XElement(ns + "UserId", userSid))),
                        new XElement(ns + "Principals", new XElement(ns + "Principal", new XAttribute("id", "Author"),
                            new XElement(ns + "UserId", userSid), new XElement(ns + "LogonType", "InteractiveToken"),
                            new XElement(ns + "RunLevel", "HighestAvailable"))),
                        new XElement(ns + "Settings", new XElement(ns + "MultipleInstancesPolicy", "IgnoreNew"),
                            new XElement(ns + "DisallowStartIfOnBatteries", "false"),
                            new XElement(ns + "StopIfGoingOnBatteries", "false"),
                            new XElement(ns + "ExecutionTimeLimit", "PT0S")),
                        new XElement(ns + "Actions", new XAttribute("Context", "Author"),
                            new XElement(ns + "Exec", new XElement(ns + "Command", exe),
                                new XElement(ns + "WorkingDirectory", AppContext.BaseDirectory)))));
                doc.Save(XmlPath);
                if (!Run("/Create", "/TN", task, "/XML", XmlPath, out _, out var error))
                {
                    _log.Warn("Autostart", "Task not created: " + error);
                    return false;
                }
                File.WriteAllText(RegisteredPath, exe, new UTF8Encoding(false));
                _log.Info("Autostart", "Opt-in per-user elevated login task created.");
                return true;
            }
            if (existing is null) return true;
            if (!Owned(existing))
            {
                _log.Warn("Autostart", "Task target or ownership differs; refusing deletion.");
                return false;
            }
            if (!Run("/Delete", "/F", "/TN", task, out _, out var deleteError))
            {
                _log.Warn("Autostart", "Could not remove owned task: " + deleteError);
                return false;
            }
            if (File.Exists(RegisteredPath)) File.Delete(RegisteredPath);
            _log.Info("Autostart", "Owned login task removed.");
            return true;
        }
        catch (Exception ex)
        {
            _log.Warn("Autostart", "Operation safely cancelled: " + ex.Message);
            return false;
        }
    }

    private static bool Run(string a, string b, string c, string d, out string output, out string error)
        => Run([a,b,c,d], out output, out error);
    private static bool Run(string a, string b, string c, string d, string e, out string output, out string error)
        => Run([a,b,c,d,e], out output, out error);
    private static bool Run(string[] args, out string output, out string error)
    {
        using var p = new Process();
        p.StartInfo = new ProcessStartInfo("schtasks.exe")
        {
            UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardOutput = true, RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8,
        };
        foreach (string arg in args) p.StartInfo.ArgumentList.Add(arg);
        p.Start();
        output = p.StandardOutput.ReadToEnd();
        error = p.StandardError.ReadToEnd();
        if (!p.WaitForExit(15000)) { try { p.Kill(); } catch (InvalidOperationException) { } return false; }
        return p.ExitCode == 0;
    }
}
