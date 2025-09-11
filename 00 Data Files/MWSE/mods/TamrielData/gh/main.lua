-- Script for allowing Graphic Herbalism to affect containers that it otherwise wouldn't
local common = require("tamrielData.common")
event.register(tes3.event.initialized, function()
    if common.gh_config then

		--common.gh_config.blacklist["t_mw_fauna_ventworm_01"] = false
		--common.gh_config.blacklist["t_mw_fauna_ventworm_02"] = false
		--common.gh_config.blacklist["t_mw_fauna_ventworm_03"] = false
		--common.gh_config.blacklist["t_mw_fauna_ventworm_04"] = false
		--common.gh_config.blacklist["t_pi_fauna_fishslvspd1"] = false
		--common.gh_config.blacklist["t_pi_fauna_fishslvspd2"] = false
		--common.gh_config.blacklist["t_pi_fauna_fishslvspd3"] = false

		common.gh_config.whitelist["t_mw_fauna_ventworm_01"] = true
		common.gh_config.whitelist["t_mw_fauna_ventworm_02"] = true
		common.gh_config.whitelist["t_mw_fauna_ventworm_03"] = true
		common.gh_config.whitelist["t_mw_fauna_ventworm_04"] = true
		common.gh_config.whitelist["t_pi_fauna_fishslvspd1"] = true
		common.gh_config.whitelist["t_pi_fauna_fishslvspd2"] = true
		common.gh_config.whitelist["t_pi_fauna_fishslvspd3"] = true

    end
end)