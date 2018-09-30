
import sys
import os
import multiprocessing
from pathlib import Path
import shutil
import subprocess
from distutils.dir_util import copy_tree

def build_package():
    build_dir = Path("build").resolve()

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    build_dir = build_dir.resolve() # Try resolving after the path now exists
    print("Using build_dir =", build_dir)

    target_dir = build_dir.joinpath("dependencies")
    target_dir.mkdir(parents=True)

    include_dir = target_dir.joinpath("include")
    include_dir.mkdir()

    lib_dir = target_dir.joinpath("lib")
    lib_dir.mkdir()

    bin_dir = target_dir.joinpath("bin")
    bin_dir.mkdir()

    licenses_dir = target_dir.joinpath("licenses")
    licenses_dir.mkdir()

    build_breakpad(build_dir, include_dir, lib_dir, licenses_dir)
    build_zlib(build_dir, include_dir, lib_dir, bin_dir)
    extract_datpack(build_dir, bin_dir)
    extract_pybind11(build_dir, include_dir, lib_dir, licenses_dir)
    extract_ffmpeg(build_dir, include_dir, lib_dir, bin_dir, licenses_dir)
    build_minhook(build_dir, include_dir, lib_dir, licenses_dir)
    build_googletest(build_dir, include_dir, lib_dir, licenses_dir)
    build_libjpegturbo(build_dir, include_dir, lib_dir, licenses_dir)
    build_python(build_dir, include_dir, lib_dir, bin_dir, target_dir, licenses_dir)

    # Compress dependencies archive using 7z (no 7z archive support)
    print("Compressing dependencies")
    subprocess.run(["7za", "a", "dependencies.7z", "dependencies"], check=True, cwd=str(build_dir))

def extract_datpack(build_dir, bin_dir):
    print("Adding datpack")
    
    shutil.unpack_archive("datpack.zip", str(build_dir))
    
    f = build_dir.joinpath("datpack/datpack.exe")
    shutil.copy(f, str(bin_dir))
    f = build_dir.joinpath("datpack/zlib.dll")
    shutil.copy(f, str(bin_dir))
    
    
    
def build_zlib(build_dir, include_dir, lib_dir, bin_dir):
    print("Adding zlib")

    shutil.unpack_archive("zlib-1.2.11.tar.gz", str(build_dir))
    src_dir = next(build_dir.glob("zlib-*"))

    # Force zlib to use the static CRT
    with src_dir.joinpath("CMakeLists.txt").open("at") as fh:
        fh.write("""
        # Enforce use of static CRT
foreach (flag_var CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELWITHDEBINFO)
    string(REPLACE "/MD" "-MT" ${flag_var} "${${flag_var}}")
endforeach()
        """)

    install_dir = build_dir.joinpath("zlib_install")

    def build(build_type):
        # Build debug version of library
        print(f"Building with CMAKE_BUILD_TYPE={build_type}")
        build_dir = src_dir.joinpath("build_" + build_type.lower())
        build_dir.mkdir()
        subprocess.run(["cmake", "-GNMake Makefiles", 
            "-DCMAKE_BUILD_TYPE=" + build_type, 
            "-DCMAKE_INSTALL_PREFIX=" + str(install_dir),
            ".."], cwd=str(build_dir), check=True)
        subprocess.run(["nmake"], cwd=str(build_dir), check=True)
        subprocess.run(["nmake", "install"], cwd=str(build_dir), check=True)       

        # Save the PDBs, those are not installed to the install_dir
        for f in build_dir.glob("zlib*.pdb"):
            shutil.copy(f, lib_dir)

    build("DEBUG")
    build("RELWITHDEBINFO")

    for f in install_dir.glob("bin/*"):
        shutil.copy(f, bin_dir)
    for f in install_dir.glob("lib/*"):
        shutil.copy(f, lib_dir)
    for f in install_dir.glob("include/*"):
        shutil.copy(f, include_dir)

def extract_pybind11(build_dir, include_dir, lib_dir, licenses_dir):
    print("Adding pybind11")

    shutil.unpack_archive("pybind11-2.2.4.tar.gz", str(build_dir))
    src_dir = next(build_dir.glob("pybind11-*"))
    shutil.copytree(src_dir.joinpath("include/pybind11"), include_dir.joinpath("pybind11"))

    shutil.copy(src_dir.joinpath("LICENSE"), licenses_dir.joinpath("pybind11.txt"))

def extract_ffmpeg(build_dir, include_dir, lib_dir, bin_dir, licenses_dir):
    print("Adding ffmpeg")
    shutil.unpack_archive("ffmpeg-3.4.1-win32-dev.zip", str(build_dir))
    dev_dir = next(build_dir.glob("ffmpeg-*-dev"))
    for lib_file in dev_dir.joinpath("lib").glob("*.lib"):
        shutil.copy(lib_file, lib_dir)
    copy_tree(str(dev_dir.joinpath("include")), str(include_dir))

    shutil.unpack_archive("ffmpeg-3.4.1-win32-shared.zip", str(build_dir))
    shared_dir = next(build_dir.glob("ffmpeg-*-shared"))
    for f in shared_dir.glob("bin/*"):
        shutil.copy(f, bin_dir)

    shutil.copy(dev_dir.joinpath("LICENSE.txt"), licenses_dir.joinpath("ffmpeg-license.txt"))
    shutil.copy(dev_dir.joinpath("README.txt"), licenses_dir.joinpath("ffmpeg-readme.txt"))

def build_breakpad(build_dir, include_dir, lib_dir, licenses_dir):
    print("Building breakpad client")

    print("Uncompressing breakpad")
    breakpad_dir = build_dir.joinpath("breakpad")
    shutil.unpack_archive("breakpad-9bcfabca.zip", str(breakpad_dir))

    gyp_dir = build_dir.joinpath("gyp_dir")
    shutil.unpack_archive("gyp-5e2b3dd.tar.gz", str(gyp_dir))

    src_dir = breakpad_dir.joinpath("src")

    def build(build_type):
        print(f"Building with CMAKE_BUILD_TYPE={build_type}")        
        cmake_build_dir = build_dir.joinpath("crash_reporting_" + build_type.lower())
        shutil.copytree("crash_reporting", cmake_build_dir)
        subprocess.run(["cmake", "-GNMake Makefiles", 
            "-DCMAKE_BUILD_TYPE=" + build_type, 
            "-DBREAKPAD_DIR=" + str(src_dir),
            "."], cwd=str(cmake_build_dir), check=True)
        subprocess.run(["nmake"], cwd=str(cmake_build_dir), check=True)

        for f in cmake_build_dir.glob("*.lib"):
            shutil.copy(f, lib_dir)
        for f in cmake_build_dir.glob("*.pdb"):
            shutil.copy(f, lib_dir)

    build("DEBUG")
    build("RELWITHDEBINFO")

    shutil.copy(breakpad_dir.joinpath("LICENSE"), licenses_dir.joinpath("breakpad.txt"))
    shutil.copy("crash_reporting/crash_reporting.h", include_dir)

    # we rebuild the binaries to make use of the DIA SDK included in our version of visual studio
    tools_dir = breakpad_dir.joinpath("src/tools/windows")
    # Put Python 2.7 into the Path because gyp is incompatible with Python 3 (boo!)
    gyp_env = os.environ.copy()
    gyp_env["PATH"] = "C:\\Python27;" + os.environ["PATH"]
    gyp_env["GYP_MSVS_VERSION"] = "2017"
    subprocess.run([str(gyp_dir.joinpath("gyp")), "tools_windows.gyp"], env=gyp_env, shell=True, check=True, cwd=str(tools_dir))
    # We are not using check=True here because this build will fail currently due to broken googletest dependencies
    subprocess.run(["msbuild", "tools_windows.sln", "/p:Configuration=Release", "/p:Platform=Win32", "/t:Clean,Build"], check=False, cwd=str(tools_dir))

    bin_dir = build_dir.joinpath("dependencies/bin")
    bin_dir.mkdir(exist_ok=True)
    for bin_file in breakpad_dir.glob("src/tools/windows/Release/*.exe"):
        shutil.copy(bin_file, bin_dir)

def build_minhook(build_dir, include_dir, lib_dir, licenses_dir):
    print("Building minhook")
    shutil.unpack_archive("minhook-1.3.3.tar.gz", str(build_dir))
    src_dir = next(build_dir.glob("minhook-*")).resolve()

    # Copy over minhook CMakeLists.txt
    shutil.copy("minhook/CMakeLists.txt", src_dir)

    def build(build_type):
        # Build debug version of library
        print(f"Building with CMAKE_BUILD_TYPE={build_type}")
        build_dir = src_dir.joinpath("build_" + build_type.lower())
        build_dir.mkdir()
        subprocess.run(["cmake", "-GNMake Makefiles", 
            "-DCMAKE_BUILD_TYPE=" + build_type, 
            ".."], cwd=str(build_dir), check=True)
        subprocess.run(["nmake"], cwd=str(build_dir), check=True)

        for f in build_dir.glob("*.lib"):
            shutil.copy(f, lib_dir)
        for f in build_dir.glob("*.pdb"):
            shutil.copy(f, lib_dir)

    build("DEBUG")
    build("RELWITHDEBINFO")

    # Copy header files
    copy_tree(str(src_dir.joinpath("include")), str(include_dir))
    hde_dir = include_dir.joinpath("hde")
    hde_dir.mkdir()
    shutil.copy(src_dir.joinpath("src/hde/hde32.h"), hde_dir)
    shutil.copy(src_dir.joinpath("src/hde/pstdint.h"), hde_dir)
    shutil.copy(src_dir.joinpath("src/trampoline.h"), include_dir)

    shutil.copy(src_dir.joinpath("LICENSE.txt"), licenses_dir.joinpath("minhook.txt"))

def build_libjpegturbo(build_dir, include_dir, lib_dir, licenses_dir):
    print("Building libjpeg-turbo")
    shutil.unpack_archive("libjpeg-turbo-1.5.3.tar.gz", str(build_dir))
    jpeg_dir = next(build_dir.glob("libjpeg-turbo-*")).resolve()

    # Modify CMakeLists.txt to get separate .lib naming for debug/release and also get a pdb file for the static library
    with jpeg_dir.joinpath("CMakeLists.txt").open("at") as fh:
        fh.write("""\nset_target_properties(turbojpeg-static PROPERTIES COMPILE_PDB_NAME turbojpeg-static COMPILE_PDB_NAME_DEBUG turbojpeg-static_d DEBUG_POSTFIX "_d")""")
        # Make sure the PDB is also copied along during the nmake install command
        fh.write("""\ninstall(FILES ${CMAKE_CURRENT_BINARY_DIR}/turbojpeg-static$<$<CONFIG:Debug>:_d>.pdb DESTINATION lib)""")

    # Extract nasm
    shutil.unpack_archive("nasm-2.13.02-win32.zip", str(build_dir))
    nasm_exe = next(build_dir.glob("nasm-*/nasm.exe")).resolve()

    # Cmake will install debug/release files here and this is where we copy our compiled library files / header files from
    install_dir = jpeg_dir.joinpath("install")

    def build(build_type):        
        # Build debug version of library
        print(f"Building with CMAKE_BUILD_TYPE={build_type}")
        build_dir = jpeg_dir.joinpath("build_" + build_type.lower())
        build_dir.mkdir()
        subprocess.run(["cmake", "-GNMake Makefiles", 
            "-DNASM=" + str(nasm_exe), 
            # "-DWITH_CRT_DLL=on", Enable to use MSVCRT DLL version rather than static linking
            "-DWITH_JPEG7=no", 
            "-DWITH_JPEG8=no", 
            "-DENABLE_SHARED=no", 
            "-DCMAKE_BUILD_TYPE=" + build_type, 
            "-DCMAKE_INSTALL_PREFIX=" + str(install_dir), 
            ".."], cwd=str(build_dir), check=True)
        subprocess.run(["nmake"], cwd=str(build_dir), check=True)
        subprocess.run(["nmake", "install"], cwd=str(build_dir), check=True)

    build("DEBUG")
    build("RELWITHDEBINFO")

    # Copy header files
    copy_tree(str(install_dir.joinpath("include")), str(include_dir))
    for lib_file in install_dir.joinpath("lib").glob("turbo*"):
        shutil.copy(lib_file, lib_dir)

    shutil.copy(jpeg_dir.joinpath("LICENSE.md"), licenses_dir.joinpath("libjpegturbo.txt"))

def build_googletest(build_dir, include_dir, lib_dir, licenses_dir):
    print("Building google test")
    shutil.unpack_archive("googletest-5490beb.zip", str(build_dir))
    src_dir = next(build_dir.glob("googletest-*")).resolve()

    # CMake will install debug/release files here and this is where we copy our compiled library files / header files from
    install_dir = src_dir.joinpath("install")

    def build(build_type):        
        # Build debug version of library
        print(f"Building with CMAKE_BUILD_TYPE={build_type}")
        build_dir = src_dir.joinpath("build_" + build_type.lower())
        build_dir.mkdir()
        subprocess.run(["cmake", "-GNMake Makefiles", 
            "-DCMAKE_BUILD_TYPE=" + build_type, 
            "-DCMAKE_INSTALL_PREFIX=" + str(install_dir), 
            ".."], cwd=str(build_dir), check=True)
        subprocess.run(["nmake"], cwd=str(build_dir), check=True)
        subprocess.run(["nmake", "install"], cwd=str(build_dir), check=True)

    build("DEBUG")
    build("RELWITHDEBINFO")

    # Copy header files
    copy_tree(str(install_dir.joinpath("include")), str(include_dir))
    copy_tree(str(install_dir.joinpath("lib")), str(lib_dir))

    shutil.copy(src_dir.joinpath("LICENSE"), licenses_dir.joinpath("googletest.txt"))

def build_openssl(build_dir, include_dir, lib_dir, bin_dir, licenses_dir):
    print("Building OpenSSL")
    # Keep in mind to update the OPENSSL_V property below as well
    shutil.unpack_archive("openssl-1.0.2n.tar.gz", str(build_dir))
    openssl_dir = next(build_dir.glob("openssl-*")).resolve()

    # Extract nasm
    shutil.unpack_archive("nasm-2.13.02-win32.zip", str(build_dir))
    nasm_dir = next(build_dir.glob("nasm-*")).resolve()
    os.environ["PATH"] = f'"{nasm_dir}";' + os.environ["PATH"]

    subprocess.run(["perl", "Configure", "no-tests", "VC-WIN32"], check=True, cwd=str(openssl_dir))
    subprocess.run("ms\\do_nasm", check=True, cwd=str(openssl_dir), shell=True)
    subprocess.run(["nmake", "-f", "ms\\nt.mak"], check=True, cwd=str(openssl_dir))

    shutil.copy(openssl_dir.joinpath("out32/openssl.exe"), bin_dir)
    shutil.copy(openssl_dir.joinpath("out32/libeay32.lib"), lib_dir)
    shutil.copy(openssl_dir.joinpath("out32/ssleay32.lib"), lib_dir)
    shutil.copy(openssl_dir.joinpath("tmp32/lib.pdb"), lib_dir)

    copy_tree(str(openssl_dir.joinpath("inc32")), str(include_dir))

    shutil.copy(openssl_dir.joinpath("LICENSE"), licenses_dir.joinpath("openssl.txt"))
    
def build_python(build_dir, include_dir, lib_dir, bin_dir, target_dir, licenses_dir):
    # Prerequisite
    build_openssl(build_dir, include_dir, lib_dir, bin_dir, licenses_dir)

    print("Building Python")
    shutil.unpack_archive("Python-2.7.14.tar.xz", str(build_dir))
    python_dir = next(build_dir.glob("Python-*")).resolve()
    python_build_dir = python_dir.joinpath("PCbuild")

    # Apply the patch fixing several compilation problems with never VS versions and
    # also adding a few modules to the list of modules to be initialized statically
    with open("python-2.7-superstatic-build.patch", "rt") as patch_in:
        subprocess.run(["patch/patch", "-p1"], stdin=patch_in, check=True, cwd=str(python_dir))
    
    # We are including C modules using a wildcard, so we have to delete everything that we don't want
    remove_patterns = """PC/frozen_dllmain.c PC/python3dll.c PC/w9xpopen.c PC/WinMain.c PC/make_versioninfo.c PC/empty.c PC/dl_nt.c PC/_msi.c PC/generrmap.c PC/strtod.c Python/strtod.c
Python/dynload_s* Python/dynload_next.c Python/dynload_aix.c Python/dynload_dl.c Python/dynload_hpux.c Python/dynload_os2.c Python/dup2.c Python/python.c
Modules/tk*.c Modules/_tk*.c Modules/getnameinfo.c Modules/getaddrinfo.c Modules/grpmodule.c Modules/pwdmodule.c Modules/nismodule.c Modules/termios.c Modules/_gestalt.c Modules/syslogmodule.c Modules/spwdmodule.c Modules/bz2module.c Modules/readline.c Modules/ossaudiodev.c Modules/fcntlmodule.c Modules/_test* Modules/main.c Modules/getpath.c Modules/pyexpat.c Modules/_dbmmodule.c Modules/_cursesmodule.c Modules/_scproxy.c Modules/resource.c Modules/_posixsubprocess.c Modules/_elementtree.c Modules/_gdbmmodule.c Modules/getcwd.c
Python/getcwd.c
Modules/_bsddb.c Modules/_curses_panel.c Modules/glmodule.c Modules/timingmodule.c Modules/fmmodule.c Modules/flmodule.c Modules/dbmmodule.c Modules/linuxaudiodev.c Modules/sunaudiodev.c Modules/almodule.c Modules/clmodule.c Modules/dlmodule.c Modules/bsddbmodule.c Modules/gdbmmodule.c Modules/imgfile.c Modules/winsound.c
Python/dynload_beos.c Python/dynload_atheos.c Python/mactoolboxglue.c Python/sigcheck.c
Modules/_ctypes/_ctypes_test* Modules/_ctypes/libffi_msvc/types.c
Modules/zlib/minigzip.c Modules/zlib/example.c Modules/zlib/gzclose.c Modules/zlib/gzlib.z Modules/zlib/gzread.c Modules/zlib/gzwrite.c
Modules/cdmodule.c Modules/sgimodule.c Modules/svmodule.c
Parser/pgen.c Parser/pgenmain.c Parser/printgrammar.c Parser/tokenizer_pgen.c Parser/intrcheck.c
Modules/atexitmodule.c""".split()

    for glob_pattern in remove_patterns:
        for f in python_dir.glob(glob_pattern):
            f.unlink()

    # Overwrite project file which sets the platform toolkit to VS2017, and also adds the 
    # C files needed for the modules we want to have embedded
    shutil.copyfile("python.vcxproj", python_build_dir.joinpath("python.vcxproj"))

    for config in ["Debug", "Release"]:
        print(f"Building Python {config}")
        subprocess.run(["msbuild", 
            "/m:" + str(multiprocessing.cpu_count()), 
            "python.vcxproj", 
            # These are now set in the vcxproj as well, except the Win10 SDK
            "/p:PlatformToolset=v141", # Force it to use Visual Studio 2017
            "/p:WindowsTargetPlatformVersion=10.0.14393.0", # Force it to use the Win10 SDK
            "/p:OPENSSL_V=1.0.2n;Configuration=" + config], 
            check=True, cwd=str(python_build_dir))

    # Copy compiled libs
    shutil.copy(python_build_dir.joinpath("python27.lib"), lib_dir)
    shutil.copy(python_build_dir.joinpath("python27.pdb"), lib_dir)
    shutil.copy(python_build_dir.joinpath("python27_d.lib"), lib_dir)
    shutil.copy(python_build_dir.joinpath("python27_d.pdb"), lib_dir)
    
    # Copy C includes
    shutil.copy(python_dir.joinpath("PC/pyconfig.h"), include_dir)
    copy_tree(str(python_dir.joinpath("Include")), str(include_dir))
    
    # Copy Python library, but ignore alot of unused directories
    ignore_lib_dirs = shutil.ignore_patterns("test",
        "plat-aix3",
        "plat-aix4",
        "plat-atheos",
        "plat-beos5",
        "plat-darwin",
        "plat-freebsd4",
        "plat-freebsd5",
        "plat-freebsd6",
        "plat-freebsd7",
        "plat-freebsd8",
        "plat-generic",
        "plat-irix5",
        "plat-irix6",
        "plat-linux2",
        "plat-mac",
        "plat-netbsd1",
        "plat-next3",
        "plat-os2emx",
        "plat-riscos",
        "plat-sunos5",
        "plat-unixware7",
        "multiprocessing",
        "idlelib",
        "lib2to3",
        "lib-tk",
        "email",
        "curses",
        "bsddb",
        "ensurepip",
        "distutils",
        "msilib",
        "pydoc_data",
        "sqlite3",
        "unittest",
        "wsgiref"
    )

    shutil.copytree(python_dir.joinpath("Lib"), target_dir.joinpath("python-lib"), ignore=ignore_lib_dirs)

    shutil.copy(python_dir.joinpath("LICENSE"), licenses_dir.joinpath("python.txt"))
    
if __name__ == "__main__":
    build_package()
