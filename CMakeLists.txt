cmake_minimum_required(VERSION 3.21)

project(SafeCruise LANGUAGES C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ADR-000 D-12: value-changing float optimisations are forbidden.
foreach(flags_var CMAKE_C_FLAGS CMAKE_C_FLAGS_${CMAKE_BUILD_TYPE})
    if("${${flags_var}}" MATCHES "fast-math|-Ofast|unsafe-math|finite-math|associative-math")
        message(FATAL_ERROR "${flags_var} contains a forbidden float flag (ADR-000 D-12): ${${flags_var}}")
    endif()
endforeach()

add_library(safecruise_warnings INTERFACE)
target_compile_options(safecruise_warnings INTERFACE
    -Wall -Wextra -Werror -pedantic
    -Wdouble-promotion -Wfloat-conversion)

option(SAFECRUISE_BUILD_TESTS "Build the Unity unit tests" ON)

add_subdirectory(swc)

if(SAFECRUISE_BUILD_TESTS)
    enable_testing()
    include(cmake/Unity.cmake)
    add_subdirectory(tests/unit_c)
endif()
