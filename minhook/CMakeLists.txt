
project(minhook)
cmake_minimum_required(VERSION 3.9)

set(SOURCES src/buffer.c
    src/hook.c
    src/trampoline.c
    src/hde/hde32.c
)

# Enforce use of static CRT
foreach (flag_var CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELWITHDEBINFO)
    string(REPLACE "/MD" "-MT" ${flag_var} "${${flag_var}}")
endforeach()

set(CMAKE_DEBUG_POSTFIX _d)

add_library(minhook STATIC ${SOURCES})
set_target_properties(minhook PROPERTIES COMPILE_PDB_NAME minhook COMPILE_PDB_NAME_DEBUG minhook_d)
