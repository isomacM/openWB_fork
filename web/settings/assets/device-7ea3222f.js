import{D as d}from"./HardwareInstallation-a0083e3a.js";import{_ as c,u as t,k as m,l,D as n,N as i,y as s}from"./vendor-f2b8aa6f.js";import"./vendor-fortawesome-71546160.js";import"./index-b0e5e618.js";import"./vendor-bootstrap-4ad604fa.js";import"./vendor-jquery-d3cb8fad.js";import"./vendor-axios-65ecee4b.js";import"./vendor-sortablejs-2f1828d0.js";import"./dynamic-import-helper-be004503.js";const u={name:"DeviceVZLogger",mixins:[d]},_={class:"device-vzlogger"};function g(e,o,v,f,b,h){const r=t("openwb-base-heading"),a=t("openwb-base-text-input");return m(),l("div",_,[n(r,null,{default:i(()=>[s(" Einstellungen für VZLogger ")]),_:1}),n(a,{title:"IP oder Hostname",subtype:"host",required:"","model-value":e.device.configuration.ip_address,"onUpdate:modelValue":o[0]||(o[0]=p=>e.updateConfiguration(p,"configuration.ip_address"))},{help:i(()=>[s(" Bei Angabe des Ports muss auch das Schema mit angegeben werden: http://ip:port ")]),_:1},8,["model-value"])])}const N=c(u,[["render",g],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/vzlogger/vzlogger/device.vue"]]);export{N as default};