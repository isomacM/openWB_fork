import{C as d}from"./HardwareInstallation-a0083e3a.js";import{_ as u,u as a,k as p,l as m,D as r,N as i,y as t,x as c}from"./vendor-f2b8aa6f.js";import"./vendor-fortawesome-71546160.js";import"./index-b0e5e618.js";import"./vendor-bootstrap-4ad604fa.js";import"./vendor-jquery-d3cb8fad.js";import"./vendor-axios-65ecee4b.js";import"./vendor-sortablejs-2f1828d0.js";import"./dynamic-import-helper-be004503.js";const g={name:"DeviceJsonInverter",mixins:[d]},w={class:"device-json-inverter"},_=c("br",null,null,-1);function f(e,n,b,h,v,x){const l=a("openwb-base-heading"),s=a("openwb-base-text-input");return p(),m("div",w,[r(l,null,{default:i(()=>[t(" Einstellungen für JSON Wechselrichter ")]),_:1}),r(s,{title:"Abfrage für Leistung",subtype:"text",required:"","model-value":e.component.configuration.jq_power,"onUpdate:modelValue":n[0]||(n[0]=o=>e.updateConfiguration(o,"configuration.jq_power"))},{help:i(()=>[t(' Zur Analyse der Werte aus dem json-Objekt wird jq benutzt. Ist die Json Antwort z.B. {"PowerInstalledPeak":4655, "PowerProduced":132, "PowerOut":897.08172362555717, "PowerSelfSupplied":234.9182763744428} So muss hier .PowerOut eingetragen werden. '),_,t(" Es wird vom Server eine Zahl mit oder ohne Nachkommastellen (Float, Integer) und einem Punkt als Dezimaltrennzeichen erwartet, welche die aktuelle Leistung in Watt darstellt. Produzierte Leistung muss ein negatives Vorzeichen haben. (In bestimmten Konstellationen, z.B. wenn ein Hybridsystem über einen zweiten Wechselrichter geladen wird, hat die Leistung ein positives Vorzeichen.) ")]),_:1},8,["model-value"]),r(s,{title:"Abfrage für Zählerstand",subtype:"text","model-value":e.component.configuration.jq_exported,"onUpdate:modelValue":n[1]||(n[1]=o=>e.updateConfiguration(o,"configuration.jq_exported"))},{help:i(()=>[t(" Wird dieses Feld leer gelassen, dann werden Zählerstände intern simuliert. ")]),_:1},8,["model-value"])])}const N=u(g,[["render",f],["__file","/opt/openWB-dev/openwb-ui-settings/src/components/devices/generic/json/inverter.vue"]]);export{N as default};