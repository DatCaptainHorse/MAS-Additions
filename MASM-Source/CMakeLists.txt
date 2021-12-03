cmake_minimum_required(VERSION 3.20)

# vcpkg automation setup #
set(VCPKG_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg")
set(ENV{VCPKG_OVERLAY_TRIPLETS} "${CMAKE_CURRENT_SOURCE_DIR}/Custom-Triplets/")
include("Submodules/Automate-VCPKG/automate-vcpkg.cmake")
if(AWFUL_HACK_TO_BUILD_ON_BINS_SYSTEM)
  # Yes, I'm well aware that this is terrible. Sometimes the world forces your hand.
  # Use this if you hate MSVC and are using something like Clang instead. YMMV with
  # MinGW.
  message(STATUS "Building release VCPKG packages only. I hope you know what you're doing (and using Clang).")
  set(VCPKG_TRIPLET "x64-windows-bin")
endif()
vcpkg_bootstrap()

project(
  "Monika After Story Module"
  VERSION 1.0.0
  LANGUAGES CXX
)

# grab packages #
vcpkg_install_packages(python3 spdlog)
find_package(Python3 COMPONENTS Development REQUIRED)
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR AWFUL_HACK_TO_BUILD_ON_BINS_SYSTEM)
  set(fmt_DIR "${VCPKG_ROOT}/installed/${VCPKG_TRIPLET}/share/fmt")
  set(spdlog_DIR "${VCPKG_ROOT}/installed/${VCPKG_TRIPLET}/share/spdlog")
endif()
find_package(spdlog CONFIG REQUIRED)


set(MASM_SOURCES
"Source/main.cpp"
"Source/utilities.h"
"Source/pythonscript.h"
"Source/python_manager.h"
"Source/python_manager.cpp")

add_executable(MASM ${MASM_SOURCES})

target_include_directories(MASM
  PRIVATE
	"Source/"
)

target_link_libraries(MASM
  PRIVATE
	$<$<CXX_COMPILER_ID:GNU>:stdc++fs>
  $<$<CXX_COMPILER_ID:GNU>:-Xlinker>
  $<$<CXX_COMPILER_ID:GNU>:-export-dynamic>
	Python3::Python
	spdlog::spdlog_header_only
)

target_compile_features(MASM
  PRIVATE
	cxx_std_20
)

foreach(SOURCE_FILE ${MASM_SOURCES})
  list(APPEND TO_FORMAT ${PROJECT_SOURCE_DIR}/${SOURCE_FILE})
endforeach()

add_custom_target(
  format
  COMMAND clang-format
  -i
  ${TO_FORMAT}
)