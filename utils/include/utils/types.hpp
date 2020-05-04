#pragma once

#include <string>
#include <map>
#include <deque>

#include <msrm_utils/output.hpp>

namespace mios {

struct SoundCmd{
    SoundCmd(const std::string& file,bool update=true,double f=0){
        this->file=file;
        this->update=update;
        this->f=f;
    }
    std::string file;
    bool update;
    double f;
};

struct LED{
    std::tuple<unsigned,unsigned,unsigned> colors;
    unsigned tt;
};

struct LEDCmd{
    LEDCmd(double f=0){
        this->f=f;
        this->finished=false;

        LED led;
        led.colors=std::make_tuple(0,0,0);
        led.tt=1;
        this->led.insert(std::pair<std::string,LED >("far-left",led));
        this->led.insert(std::pair<std::string,LED >("left",led));
        this->led.insert(std::pair<std::string,LED >("middle",led));
        this->led.insert(std::pair<std::string,LED >("right",led));
        this->led.insert(std::pair<std::string,LED >("far-right",led));
    }

    bool set_led(const std::string& id, int r, int g, int b){
        if(r>255) r=255;
        if(g>255) g=255;
        if(b>255) b=255;
        if(r<1) r=1;
        if(g<1) g=1;
        if(b<1) b=1;
        if(this->led.find(id)==this->led.end()){
            msrm_utils::print_error("No LED with id "+id+".");
            return false;
        }
        this->led[id].colors=std::make_tuple(r,g,b);
        return true;
    }

    void set_all_led(int r, int g, int b){
        for(const auto& l : this->led){
            this->set_led(l.first,r,g,b);
        }
    }

    void limit_colors(){
        for(auto& l : this->led){
            if(std::get<0>(l.second.colors)>255){
                std::get<0>(l.second.colors)=255;
            }
            if(std::get<0>(l.second.colors)<1){
                std::get<0>(l.second.colors)=1;
            }
            if(std::get<1>(l.second.colors)>255){
                std::get<1>(l.second.colors)=255;
            }
            if(std::get<1>(l.second.colors)<1){
                std::get<1>(l.second.colors)=1;
            }
            if(std::get<2>(l.second.colors)>255){
                std::get<2>(l.second.colors)=255;
            }
            if(std::get<2>(l.second.colors)<1){
                std::get<2>(l.second.colors)=1;
            }
        }
    }

    std::map<std::string,LED> led;
    double f;
    bool finished;
};

struct Telemetry{
    Telemetry(){
        q[0]={0,0,0,0,0,0,0};
        tau_ext[0]={0,0,0,0,0,0,0};
    }
    std::deque<std::array<double,7> > q;
    std::deque<std::array<double,7> > tau_ext;
};

}
