
project(crash_reporting)
cmake_minimum_required(VERSION 3.9)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}")

set(BREAKPAD_DIR breakpad/src CACHE PATH "Path to breakpad source directory")

set(BREAKPAD_SOURCES
    ${BREAKPAD_DIR}/client/windows/handler/exception_handler.cc
    ${BREAKPAD_DIR}/client/windows/crash_generation/crash_generation_client.cc
    ${BREAKPAD_DIR}/common/windows/guid_string.cc
)

set(SOURCES crash_reporting.cpp crash_reporting.h)

# Enforce use of static CRT
foreach (flag_var CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELWITHDEBINFO)
    string(REPLACE "/MD" "-MT" ${flag_var} "${${flag_var}}")
endforeach()

set(CMAKE_DEBUG_POSTFIX _d)

add_library(crash_reporting STATIC ${SOURCES} ${BREAKPAD_SOURCES})
set_target_properties(crash_reporting PROPERTIES COMPILE_PDB_NAME crash_reporting COMPILE_PDB_NAME_DEBUG crash_reporting_d)
add_definitions(-DUNICODE)
include_directories(${BREAKPAD_DIR})

find_package(DiaSDK REQUIRED) # Used for constants and declarations.

set(DUMP_SYMS_SRC
    ${BREAKPAD_DIR}/tools/windows/dump_syms/dump_syms.cc
    ${BREAKPAD_DIR}/common/windows/dia_util.cc
    ${BREAKPAD_DIR}/common/windows/guid_string.cc
    ${BREAKPAD_DIR}/common/windows/omap.cc
    ${BREAKPAD_DIR}/common/windows/pdb_source_line_writer.cc
    ${BREAKPAD_DIR}/common/windows/pe_source_line_writer.cc
    ${BREAKPAD_DIR}/common/windows/string_utils.cc
    ${BREAKPAD_DIR}/common/windows/pe_util.cc
)
add_executable(dump_syms ${DUMP_SYMS_SRC})
target_include_directories(dump_syms PRIVATE ${DIASDK_INCLUDE_DIRS})
target_link_libraries(dump_syms PRIVATE ${LIBRARIES} ${DIASDK_LIBRARIES} Imagehlp.lib Dbghelp.lib)
