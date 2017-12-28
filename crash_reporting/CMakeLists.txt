
project(crash_reporting)
cmake_minimum_required(VERSION 3.9)

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
