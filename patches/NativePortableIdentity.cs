using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace Nexus.App.Services;

/// <summary>
/// This instance's mutex and named pipe cannot collide with another Nexus install.
/// Identity is based on the current executable directory: a moved copy gets a new
/// identity; another independent copy in a different folder can coexist.
/// No persistent host registration or launcher is needed.
/// </summary>
public static class NativePortableIdentity
{
    public static string Suffix { get; } = MakeSuffix();
    private static string MakeSuffix()
    {
        string path = Path.GetFullPath(AppContext.BaseDirectory)
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            .ToUpperInvariant();
        byte[] bytes = SHA256.HashData(Encoding.UTF8.GetBytes(path));
        return Convert.ToHexString(bytes)[..16];
    }
}
