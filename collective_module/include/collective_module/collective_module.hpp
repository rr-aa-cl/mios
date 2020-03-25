#pragma once

#include <map>
#include <set>
#include <string>
#include <atomic>
#include <thread>

#include "knowledge_base/concepts.hpp"

namespace mios {

class KnowledgeBase;

class CollectiveModule{
public:
    CollectiveModule();
    ~CollectiveModule();

    void cycle();

    bool add_robot(Robot r);

    bool has_robot(std::string robot);
    bool whitelist_robot(std::string robot);
    bool blacklist_robot(std::string robot);

    bool is_primary();
    void set_as_primary();
    void set_as_secondary(std::string ip_primary);

    std::map<std::string, Robot *> *get_robots();
    std::string get_primary_ip();

    void lock_negotiations();
    void unlock_negotiations();

private:

    bool broadcast();
    bool listen();

    bool remove_robot(std::string robot);

    std::map<std::string,Robot*> _robots;
    std::set<std::string> _black_list_robots;

    std::thread _thr_broadcast;
    std::thread _thr_listen;
    std::mutex _mtx_negotiations;
    std::mutex _mtx_queue;

    KnowledgeBase* _kb;

    std::atomic<bool> _flag_primary;
    std::atomic<bool> _flag_hear_primary;
    std::string _current_primary;
    unsigned _cnt_silence;

    std::list<std::string> _queue_primaries;

    unsigned _len_msg;
};

}
