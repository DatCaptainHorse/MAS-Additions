add_rules("mode.debug", "mode.release")

set_rules("c++")
set_languages("c++20")

add_requires("spdlog")
add_requires("python 3.10.*", { configs = { shared = true } })

set_installdir("$(buildir)/install/")

target("MASM")
    set_kind("binary")
    add_files("Source/*.cpp")
    add_packages("python", "spdlog")
    add_includedirs("Source/")
