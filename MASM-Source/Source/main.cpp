// Diet-coke MASM that had Singularity Engine ripped out of it

#include <vector>
#include <csignal>
#include <filesystem>
#include <thread>
#include <memory>

#ifdef _WIN32
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef NOGDI
#define NOGDI
#endif
#include <Windows.h>
#endif

#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>

#include <python_manager.h>
#include <pythonscript.h>

using namespace MASM;

volatile sig_atomic_t s_Close = 0;
void signal_close(int sig) {
	s_Close = 1;
}

#if _WIN32
BOOL WINAPI windowsConsoleHandler(const DWORD signal) {
	switch (signal) {
		case CTRL_C_EVENT:
		case CTRL_CLOSE_EVENT:
			s_Close = 1;
			Sleep(10000); // 10 seconds before we force-close..
			return true;
		default:
			return false;
	}
}
#endif

int main(int argc, char** argv) {
#ifdef _WIN32
	auto console = GetStdHandle(STD_INPUT_HANDLE);
	SetConsoleMode(console, ENABLE_EXTENDED_FLAGS);
	SetConsoleCtrlHandler(windowsConsoleHandler, true);
	signal(SIGINT, &signal_close);
	signal(SIGTERM, &signal_close);
#else
	struct sigaction signalHandler;
	signalHandler.sa_handler = signal_close;
	sigemptyset(&signalHandler.sa_mask);
	signalHandler.sa_flags = 0;
	sigaction(SIGINT, &signalHandler, NULL);
#endif
	try {
		auto consoleSink = std::make_shared<spdlog::sinks::stdout_color_sink_st>();
		auto fileSink = std::make_shared<spdlog::sinks::basic_file_sink_st>("masm_log.txt", true);
		spdlog::set_default_logger(std::make_shared<spdlog::logger>("masm_logger", spdlog::sinks_init_list({ consoleSink, fileSink })));
		spdlog::flush_on(spdlog::level::info);
	} catch (const spdlog::spdlog_ex& e) {
		std::cout << e.what() << std::endl;
	}

	spdlog::set_pattern("[%^%l%$] %v");
	
	auto masmPath = std::filesystem::path(argv[0]).parent_path();
	spdlog::info("MASM path: {}", masmPath.string());

	if (!PythonManager::Init(masmPath)) {
		spdlog::error("Failed to initialize, closing");
		spdlog::shutdown();
		return 1;
	}
	
	std::vector<PythonScript> loadedScripts;
	for (const auto& f : std::filesystem::directory_iterator(masmPath / "scripts")) {
		if (f.path().extension() == ".py") {
			spdlog::info("Found Python script: {}", f.path().filename().string());
			loadedScripts.emplace_back(f.path().string());
		}
	}

	spdlog::set_pattern("%v");
	spdlog::info("");
	spdlog::set_pattern("[%^%l%$] %v");

	for (auto& script : loadedScripts)
		script.callStart();

	auto cycleTime = 0.0;
	auto updateCycle = 0.0;
	auto sleepTiming = std::chrono::steady_clock::now();
	auto time = std::chrono::high_resolution_clock::now();
	auto oldTime = std::chrono::duration_cast<std::chrono::duration<double, std::milli>>(std::chrono::high_resolution_clock::now() - time).count() / 1000.0;
	while (s_Close == 0) {
		sleepTiming += std::chrono::microseconds(std::chrono::seconds(1)) / 100;

		auto newTime = std::chrono::duration_cast<std::chrono::duration<double, std::milli>>(std::chrono::high_resolution_clock::now() - time).count() / 1000.0;
		cycleTime = newTime - oldTime;
		if (cycleTime > 0.25)
			cycleTime = 0.25;

		updateCycle += cycleTime;
		while (updateCycle >= 1.0 / 100.0) {
			for (auto& script : loadedScripts)
				script.callUpdate();

			updateCycle -= 1.0 / 100.0;
		}

		oldTime = newTime;

		std::this_thread::sleep_until(sleepTiming);
	}
	
	for (auto& script : loadedScripts)
		script.callQuit();

	spdlog::set_pattern("%v");
	spdlog::info("");
	spdlog::set_pattern("[%^%l%$] %v");
	
	spdlog::info("Cleaning up");
	PythonManager::Clean();

	spdlog::info("Bye!");
	spdlog::shutdown();

	return 0;
}