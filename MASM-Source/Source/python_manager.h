#pragma once

#include <string>
#include <filesystem>

namespace MASM {

	class PythonManager 
	{
	private:
		static bool m_Init;

	public:
		static bool Init(std::filesystem::path path);
		static void Clean();
	};
}