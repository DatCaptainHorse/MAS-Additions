#pragma once

#include <string>

#include <Python.h>
#include <spdlog/spdlog.h>

#include <utilities.h>

namespace MASM {

	class PythonScript
	{
	private:
		PyObject* m_Module = nullptr;
		PyObject *m_FuncStart = nullptr, *m_FuncUpdate = nullptr,
				 *m_FuncQuit = nullptr;

	public:
		inline PythonScript(const std::string& file)
		{
			auto [filepath, filename] = string_split_path_file(file);

			// Check if file has valid extension
			const auto split = string_split(filename, '.');
			if (split.back() != "py") {
				spdlog::error("Invalid filename : {}", filename);
				return;
			}

			m_Module = PyImport_ImportModule(
				split[0].c_str()); // Import the Python module (script)

			if (m_Module == nullptr)
				PyErr_Print();
			else {
				if (PyObject_HasAttrString(m_Module, "Start"))
					m_FuncStart = PyObject_GetAttrString(m_Module, "Start");

				if (PyObject_HasAttrString(m_Module, "Update"))
					m_FuncUpdate = PyObject_GetAttrString(m_Module, "Update");

				if (PyObject_HasAttrString(m_Module, "Quit"))
					m_FuncQuit = PyObject_GetAttrString(m_Module, "Quit");
			}

			if (PyErr_Occurred())
				PyErr_Print();
		}

		inline void callStart()
		{
			if (m_FuncStart != nullptr)
				PyObject_CallObject(m_FuncStart, nullptr);
		}

		inline void callUpdate()
		{
			if (m_FuncUpdate != nullptr)
				PyObject_CallObject(m_FuncUpdate, nullptr);
		}

		inline void callQuit()
		{
			if (m_FuncQuit != nullptr)
				PyObject_CallObject(m_FuncQuit, nullptr);
		}
	};
} // namespace MASM