
for /f "usebackq tokens=*" %%i in (`vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
  set InstallDir=%%i
)

call "%InstallDir%\Common7\Tools\vsdevcmd.bat" -arch=x86 -host_arch=x86

python build_package.py
