#include <python_manager.h>

#include <Python.h>
#include <spdlog/spdlog.h>

namespace MASM {

	bool PythonManager::m_Init = false;

	bool PythonManager::Init(std::filesystem::path path)
	{
		if (m_Init)
			return true;

		spdlog::info("Initializing Python");

		PyStatus status;
		
		PyPreConfig preConf;
		PyPreConfig_InitIsolatedConfig(&preConf);
		preConf.utf8_mode = 1;
		status = Py_PreInitialize(&preConf);

		PyConfig config;
		PyConfig_InitIsolatedConfig(&config);
		config.user_site_directory = 0;
		config.module_search_paths_set = 1;
		config.write_bytecode = 0;
		config.configure_c_stdio = 1;
		config.install_signal_handlers = 0;

		// Find embedded Python folder
		auto embeddedPath = path / "python39";
		if (!std::filesystem::exists(embeddedPath)) {
			spdlog::error("Could not locate embedded python directory");
			return false;
		}
		
		spdlog::info("Embedded Python path: {}", embeddedPath.string());
		status = PyConfig_SetString(&config, &config.home, embeddedPath.wstring().c_str());
		status = PyWideStringList_Append(&config.module_search_paths, embeddedPath.wstring().c_str());
		status = PyWideStringList_Append(&config.module_search_paths, (embeddedPath / "Lib").wstring().c_str());
		status = PyWideStringList_Append(&config.module_search_paths, (embeddedPath / "DLLs").wstring().c_str());
		status = PyWideStringList_Append(&config.module_search_paths, path.wstring().c_str());
		status = PyWideStringList_Append(&config.module_search_paths, (path / "scripts").wstring().c_str());
		status = PyWideStringList_Append(&config.module_search_paths, (path / "python-packages").wstring().c_str());


		status = Py_InitializeFromConfig(&config);
		
		PyConfig_Clear(&config);

		m_Init = true;

		return true;
	}

	void PythonManager::Clean()
	{
		if (!m_Init)
			return;

		//Py_Finalize(); // Causes a freeze under linux, it's not needed according to documentation so.. good luck?

		m_Init = false;
	}
}