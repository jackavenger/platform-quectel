# WizIO 2019 Georgi Angelov
# http://www.wizio.eu/
# https://github.com/Wiz-IO

import os
from os.path import join
from shutil import copyfile
from SCons.Script import ARGUMENTS, DefaultEnvironment, Builder
from bg96 import upload_app

def dev_uploader(target, source, env):
    return
    #return upload_app(env.BoardConfig().get("build.core"), join(env.get("BUILD_DIR"), "program.bin"), env.get("UPLOAD_PORT")) 

def dev_header(target, source, env):
    d = source[0].path 
    print d
    f = open(d.replace("program.bin", "oem_app_path.ini"), "wb")
    f.write("/datatx/program.bin")
    f.close()

def dev_create_template(env):
    D = join(env.subst("$PROJECT_DIR"), "src")
    S = join(env.PioPlatform().get_package_dir("framework-quectel"), "templates", env.BoardConfig().get("build.core"))
    if False == os.path.isfile( join(D, "main.c") ):
        copyfile( join(S, "main.c"), join(D, "main.c") ) 
                
def dev_compiler(env):
    env.Replace(
        BUILD_DIR = env.subst("$BUILD_DIR").replace("\\", "/"),
        AR="arm-none-eabi-ar",
        AS="arm-none-eabi-as",
        CC="arm-none-eabi-gcc",
        GDB="arm-none-eabi-gdb",
        CXX="arm-none-eabi-g++",
        OBJCOPY="arm-none-eabi-objcopy",
        RANLIB="arm-none-eabi-ranlib",
        SIZETOOL="arm-none-eabi-size",
        ARFLAGS=["rc"],
        SIZEPROGREGEXP=r"^(?:\.text|\.data|\.bootloader)\s+(\d+).*",
        SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
        SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
        SIZEPRINTCMD='$SIZETOOL --mcu=$BOARD_MCU -C -d $SOURCES',
        PROGSUFFIX=".elf",  
    )

def dev_init(env, platform):
    dev_create_template(env)
    dev_compiler(env)
    framework_dir = env.PioPlatform().get_package_dir("framework-quectel")
    core = env.BoardConfig().get("build.core") 
    print "CORE", core    
    variant = env.BoardConfig().get("build.variant")  
    print "VARIANT", variant
    env.firmware = env.BoardConfig().get("build.firmware", "SDK2").upper()  #SDK2 #SDK3
    print "FIRMWARE", env.firmware
    env.base = env.BoardConfig().get("build.base", "0x40000000")    
    print "RO_BASE", env.base
    env.heap = env.BoardConfig().get("build.heap", "1048576") 
    env.Append(
       CPPDEFINES = [ # -D                         
            platform.upper(), "CORE_" + core.upper().replace("-", "_"), 
            "QAPI_TXM_MODULE", 
            "TXM_MODULE",  
            "TX_DAM_QC_CUSTOMIZATIONS",  
            "TX_ENABLE_PROFILING",  
            "TX_ENABLE_EVENT_TRACE",  
            "TX_DISABLE_NOTIFY_CALLBACKS",   
            "FX_FILEX_PRESENT",  
            "TX_ENABLE_IRQ_NESTING",   
            "TX3_CHANGES", 
            "_RO_BASE_=" + env.base,  
            "HEAP_SIZE=32768"                      
        ],        
        CPPPATH = [ # -I
            join(framework_dir, platform, core, env.firmware),
            join(framework_dir, platform, core, env.firmware, "qapi"),
            join(framework_dir, platform, core, env.firmware, "threadx_api"),             
            join(framework_dir, platform, core, "quectel"),        
            join("$PROJECT_DIR", "lib"),
            join("$PROJECT_DIR", "include")         
        ],        
        CFLAGS = [
            "-O1",
            "-marm",
            "-mcpu=cortex-a7",
            "-mfloat-abi=softfp",             
            "-std=c11",                                                 
            "-fdata-sections",      
            "-ffunction-sections",              
            "-fno-strict-aliasing",
            "-fno-zero-initialized-in-bss", 
            "-fsingle-precision-constant",                                                 
            "-Wall", 
            "-Wstrict-prototypes", 
            "-Wp,-w",                          
        ],        
        LINKFLAGS = [ 
            "-O1", 
            "-g",  
            "-marm",
            "-mcpu=cortex-a7",
            "-mfloat-abi=softfp",            
            "-Xlinker", "--defsym=_RO_BASE_=" + env.base, 
            "-Xlinker", "--gc-sections", 
            "-Wl,--gc-sections",               
            "-nostartfiles",     
            "-fno-use-cxa-atexit",
            "-fno-zero-initialized-in-bss",
            "-fmessage-length=0",
            "-ffunction-sections",
            "-fdata-sections",                               
        ],       
        LDSCRIPT_PATH = join(framework_dir, platform, core, "c.ld"), 
        LIBS = [ "gcc", "m" ],               
        BUILDERS = dict(
            ElfToBin = Builder(
                action = env.VerboseAction(" ".join([
                    "$OBJCOPY",
                    "-O",
                    "binary",
                    "$SOURCES",
                    "$TARGET",
                ]), "Building $TARGET"),
                suffix = ".bin"
            ),    
            MakeHeader = Builder( 
                action = env.VerboseAction(dev_header, "ADD HEADER"),
                suffix = ".ini"
            )       
        ), 
        UPLOADCMD = dev_uploader
    )
    libs = []      
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", platform),
            join(framework_dir, platform, core, env.firmware),
    ))    
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "_quectel"),
            join(framework_dir, "threadx", core, "quectel"),
    ))         
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "custom"), 
            join("$PROJECT_DIR", "lib"),                       
    ))         

    env.Append(LIBS = libs)   