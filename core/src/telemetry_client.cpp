#include "core/telemetry_client.hpp"

#include "cpp_utils/json.hpp"
#include "cpp_utils/network.hpp"

namespace mios {
TelemetryClient::TelemetryClient(boost::asio::io_service &io_service, boost::asio::ssl::context &context, boost::asio::ip::tcp::resolver::iterator endpoint_iterator, Telemetry &t): socket_(io_service, context){
    socket_.set_verify_mode(boost::asio::ssl::context::verify_none);
    boost::asio::async_connect(socket_.lowest_layer(), endpoint_iterator,boost::bind(&TelemetryClient::handle_connect, this,boost::asio::placeholders::error));
    this->_q=t.q[0];
    this->_tau_ext=t.tau_ext[0];
}

TelemetryClient::~TelemetryClient(){

}

void TelemetryClient::link_kb(KnowledgeBase *kb){
    this->_kb=kb;
}

void TelemetryClient::handle_connect(const boost::system::error_code &error){
    if (!error){
        socket_.async_handshake(boost::asio::ssl::stream_base::client,boost::bind(&TelemetryClient::handle_handshake, this,boost::asio::placeholders::error));
    }else{
        std::cout << "Connect failed: " << error.message() << "\n";
    }
}

void TelemetryClient::handle_handshake(const boost::system::error_code &error){
//    if (!error){
//        std::stringstream request_;

//        std::string payload="{";
//        for(unsigned i=0;i<7;i++){
//            payload+="\"A"+std::to_string(i+1)+"\":"+std::to_string(this->_q[i])+",";
//        }
//        for(unsigned i=0;i<7;i++){
//            bool contact=false;
//            if(fabs(this->_tau_ext[i])>this->_kb->get_local_memory()->access_config_user().tau_contact[i]){
//                contact=true;
//            }
//            payload+="\"F"+std::to_string(i+1)+"\":"+std::to_string(cpp_utils::sgn(this->_tau_ext[i])*contact)+",";
//        }
//        payload = payload.substr(0, payload.size()-1);
//        payload+="}";

//        unsigned content_length=payload.size();

//        request_ << "POST "<<this->_kb->get_local_memory()->access_config_system().telemetry_url<<" HTTP/1.1\r\n";
//        request_ << "Host: "<<this->_kb->get_local_memory()->access_config_system().telemetry_domain<<"\r\n";
//        request_ << "Authorization: "<<this->_kb->get_local_memory()->access_config_system().telemetry_key<<"\r\n";
//        request_ << "Accept-Encoding: *\r\n";
//        request_ << "Content-Length: "<<content_length<< "\r\n";
//        request_ << "\r\n";
//        request_ << payload;

//        boost::asio::async_write(socket_, boost::asio::buffer(request_.str()), boost::bind(&TelemetryClient::handle_write, this, boost::asio::placeholders::error, boost::asio::placeholders::bytes_transferred));
//    }else{
//        std::cout << "Handshake failed: " << error.message() << "\n";
//    }
}

void TelemetryClient::handle_write(const boost::system::error_code &error, size_t bytes_transferred){
    if (!error){
        //            boost::asio::async_read(socket_,boost::asio::buffer(reply_, bytes_transferred),boost::bind(&client::handle_read, this,boost::asio::placeholders::error,boost::asio::placeholders::bytes_transferred));
    }else{
        std::cout << "Write failed: " << error.message() << "\n";
    }
}


}
