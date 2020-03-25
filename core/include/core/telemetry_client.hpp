#pragma once

#include <boost/bind.hpp>
#include <boost/asio.hpp>
#include <boost/asio/ssl.hpp>

#include "knowledge_base/knowledge_base.hpp"
#include "utils/types.hpp"

namespace mios {

class TelemetryClient{
public:
    TelemetryClient(boost::asio::io_service& io_service, boost::asio::ssl::context& context, boost::asio::ip::tcp::resolver::iterator endpoint_iterator, Telemetry& t);
    ~TelemetryClient();

    void link_kb(KnowledgeBase* kb);

private:

    void handle_connect(const boost::system::error_code& error);
    void handle_handshake(const boost::system::error_code& error);
    void handle_write(const boost::system::error_code& error,size_t bytes_transferred);

    boost::asio::ssl::stream<boost::asio::ip::tcp::socket> socket_;
    char request_[1024];
    char reply_[1024];

    std::array<double,7> _q;
    std::array<double,7> _tau_ext;
    KnowledgeBase* _kb;
};

}
