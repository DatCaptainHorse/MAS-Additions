add_rules("mode.debug", "mode.release")

set_rules("c++")
set_languages("c++20")

add_requires("spdlog")
add_requires("python 3.10.*", { configs = { shared = true } })

-- Set special installdirs for each platform, for easier GitHub Actions usage
if is_plat("windows") then
	set_installdir("$(buildir)/install/windows/$(arch)/")
elseif is_plat("linux") then
	set_installdir("$(buildir)/install/linux/$(arch)/")
elseif is_plat("macosx") then
	set_installdir("$(buildir)/install/macosx/$(arch)/")
end

target("MASM")
    set_kind("binary")
    add_files("Source/*.cpp")
    add_packages("python", "spdlog")
    add_includedirs("Source/")
