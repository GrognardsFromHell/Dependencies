
#pragma once

namespace google_breakpad {
	class ExceptionHandler;
}

#include <memory>
#include <string>
#include <functional>

/*
	Abstracts the interface to Google breakpad
*/
class InProcessCrashReporting {
public:
	InProcessCrashReporting(const std::wstring &minidump_folder,
                            std::function<void(const std::wstring&)> crash_callback);
	~InProcessCrashReporting();

    // Helper functions to cause crashes for testing
    void DerefZeroCrash();
    void InvalidParamCrash();
    void PureCallCrash();

private:
    struct Detail;
    friend struct Detail;

    void ReportCrash(const std::wstring &minidump_file);

	std::unique_ptr<google_breakpad::ExceptionHandler> handler_;
    std::function<void(const std::wstring&)> crash_callback_;
};
