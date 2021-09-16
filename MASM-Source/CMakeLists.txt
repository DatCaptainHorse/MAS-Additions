cmake_minimum_required(VERSION 3.20)

# vcpkg automation setup #
set(VCPKG_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg")
set(ENV{VCPKG_OVERLAY_TRIPLETS} "${CMAKE_CURRENT_SOURCE_DIR}/Custom-Triplets/")
include("Submodules/Automate-VCPKG/automate-vcpkg.cmake")
vcpkg_bootstrap()

project(
  "Monika After Story Module"
  VERSION 1.0.0
  LANGUAGES CXX
)

# grab packages #
vcpkg_install_packages(python3 spdlog)
find_package(Python3 COMPONENTS Development REQUIRED)
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  set(fmt_DIR "${VCPKG_ROOT}/installed/x64-linux/share/fmt")
  set(spdlog_DIR "${VCPKG_ROOT}/installed/x64-linux/share/spdlog")
endif()
find_package(spdlog CONFIG REQUIRED)

add_executable(MASM)

target_sources(MASM
  PRIVATE
	"Source/main.cpp"
	"Source/utilities.h"
	"Source/pythonscript.h"
	"Source/python_manager.h"
	"Source/python_manager.cpp"
)

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