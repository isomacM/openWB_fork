import{C as m}from"./HardwareInstallation-a0083e3a.js";import{_ as c,u as n,k as u,l as d,D as t,N as i,y as s}from"./vendor-f2b8aa6f.js";import"./vendor-fortawesome-71546160.js";import"./index-b0e5e618.js";import"./vendor-bootstrap-4ad604fa.js";import"./vendor-jquery-d3cb8fad.js";import"./vendor-axios-65ecee4b.js";import"./vendor-sortablejs-2f1828d0.js";import"./dynamic-import-helper-be004503.js";const l={name:"DeviceMTecCounter",mixins:[m]},_={class:"device-mtec-counter"};function b(e,o,f,v,g,C){const r=n("openwb-base-heading"),a=n("openwb-base-number-input");return u(),d("div",_,[t(r,null,{default:i(()=>[s(" Einstellungen für M-Tec Zähler ")]),_:1}),t(a,{title:"Modbus ID",required:"","model-value":e.component.configuration.modbus_id,min:"1",max:"255","onUpdate:modelValue":o[0]||(o[0]=p=>e.updateConfiguration(p,"configuration.modbus_id"))},{help:i(()=>[s(" Die Standard-Modbus-ID von M-Tec ist 247 ")]),_:1},8,["model-value"])])}const N=c(l,[["render",b],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/mtec/mtec/counter.vue"]]);export{N as default};