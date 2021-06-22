function(apply_module_options MODULE)

    if(ENABLE_IPO)
        include(CheckIPOSupported)
        check_ipo_supported(RESULT result)
        if(result)
            set_target_properties(${MODULE} PROPERTIES INTERPROCEDURAL_OPTIMIZATION TRUE)
        endif()
    endif()

    if(ENABLE_UNITY_BUILD)
        set_target_properties(${MODULE} PROPERTIES UNITY_BUILD ON)
    endif()

    set_property(TARGET ${MODULE} PROPERTY POSITION_INDEPENDENT_CODE ON)


endfunction()
