import{D as a}from"./HardwareInstallation-79ea1bc6.js";import{_ as p,u as s,k as u,l as m,G as n,E as d,y as l}from"./vendor-06e11d0e.js";import"./vendor-fortawesome-3d19d475.js";import"./index-e2dbf7bf.js";import"./vendor-bootstrap-4263d7eb.js";import"./vendor-jquery-9fc083b4.js";import"./vendor-axios-22b906fb.js";import"./vendor-sortablejs-0bb60e5b.js";import"./dynamic-import-helper-be004503.js";const c={name:"DeviceSmartMe",mixins:[a]},f={class:"device-smart-me"};function v(o,e,_,b,g,w){const r=s("openwb-base-heading"),i=s("openwb-base-text-input");return u(),m("div",f,[n(r,null,{default:d(()=>e[2]||(e[2]=[l(" Einstellungen für smart-me ")])),_:1}),n(i,{title:"Benutzername",subtype:"user",required:"","model-value":o.device.configuration.user,"onUpdate:modelValue":e[0]||(e[0]=t=>o.updateConfiguration(t,"configuration.user"))},null,8,["model-value"]),n(i,{title:"Passwort",subtype:"password",required:"","model-value":o.device.configuration.password,"onUpdate:modelValue":e[1]||(e[1]=t=>o.updateConfiguration(t,"configuration.password"))},null,8,["model-value"])])}const q=p(c,[["render",v],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/smart_me/smart_me/device.vue"]]);export{q as default};