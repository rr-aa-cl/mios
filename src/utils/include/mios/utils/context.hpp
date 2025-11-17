#pragma once
#include <atomic>
#include "mios/utils/configuration.hpp"

struct MiosContext {
    // static MIOS configuration
    const mios::MiosConfiguration& config;
    
    // Represents status of SIG Signals:
    std::atomic<bool>& shutdown_signal;
    
    // Future proofing:
    // e.g., ServiceLocator& services;
    // e.g., spdlog::logger& logger;
};