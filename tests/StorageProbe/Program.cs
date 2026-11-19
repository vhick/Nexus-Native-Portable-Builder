using Nexus.Core.Persistence;

// Runs against the actual recompiled Nexus.Core at its real SDK runtime, WITHOUT
// starting elevated Nexus.exe or claiming to test WPF app startup.
string expected = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "Data"));
NexusPaths paths = NexusPaths.Default();
if (!string.Equals(Path.GetFullPath(paths.Root), expected, StringComparison.OrdinalIgnoreCase))
    throw new Exception($"NexusPaths.Default leaked outside EXE folder: {paths.Root}");
if (paths.SettingsFile.StartsWith(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData) +
    Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
    throw new Exception("Nexus settings point to user's host APPDATA");

var service = new SettingsService(paths);
service.Update(s => s with { WizardCompleted = true });
if (!File.Exists(paths.SettingsFile))
    throw new Exception("First-run Nexus settings did not persist within local Data");
var restarted = new SettingsService(paths);
if (!restarted.Current.WizardCompleted)
    throw new Exception("Nexus settings did not survive a new SettingsService instance");

Console.WriteLine("SOURCE RUNTIME STORAGE PROBE PASS: " + paths.SettingsFile);
Console.WriteLine("This tests only Nexus.Core path resolution and JSON persistence, not elevated Nexus GUI or Windows integration.");
