# Unity (ThrowTheSwitch) unit test framework, pinned by version and SHA-256.
include(FetchContent)

FetchContent_Declare(unity
    URL https://github.com/ThrowTheSwitch/Unity/archive/refs/tags/v2.7.0.tar.gz
    URL_HASH SHA256=e84eb301ca7967831e68b1728f911e87fa2d345d8ddb64f897bc2f2ee24a321c
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    # No CMakeLists.txt in this subdirectory: fetch only, do not add Unity's own build.
    SOURCE_SUBDIR do-not-add)
FetchContent_MakeAvailable(unity)

# Built here rather than through Unity's own CMakeLists so that its options stay in our hands.
add_library(unity STATIC ${unity_SOURCE_DIR}/src/unity.c)
target_include_directories(unity SYSTEM PUBLIC ${unity_SOURCE_DIR}/src)
target_compile_definitions(unity PUBLIC UNITY_INCLUDE_FLOAT UNITY_EXCLUDE_DOUBLE)

# safecruise_add_unity_test(<name> SOURCES <files...> LIBS <targets...>)
# Registers one CTest test per Unity test executable. Test functions that verify a
# requirement are named test_TC_<...> (ADR-000 D-18).
function(safecruise_add_unity_test name)
    cmake_parse_arguments(ARG "" "" "SOURCES;LIBS" ${ARGN})
    add_executable(${name} ${ARG_SOURCES})
    target_link_libraries(${name} PRIVATE unity safecruise_warnings ${ARG_LIBS})
    add_test(NAME ${name} COMMAND ${name})
endfunction()
