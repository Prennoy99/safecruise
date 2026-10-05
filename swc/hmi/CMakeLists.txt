add_library(swc_hmi STATIC Hmi.c)
target_include_directories(swc_hmi PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(swc_hmi PRIVATE safecruise_warnings)
