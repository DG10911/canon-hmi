/* CANON — Schneider Electric Industrial Engineering Corpus (structured, truth-tagged).
   HONESTY POLICY (per acquisition spec v1.0):
   • Product FAMILIES, categories, software pairings, communication protocols and standards
     below are well-established public Schneider Electric product knowledge (truth: VERIFIED).
   • Exact commercial references, register addresses, counts and URLs are NOT enumerated here
     unless widely documented; anything needing a citation is marked truth:"VERIFY" with source
     "se.com (confirm)". No live web crawl was performed in this build.
   • CANON demo assets and HMI mapping rules are marked PROPOSED and kept separate from
     Schneider product facts. Never present PROPOSED as VERIFIED. */
window.SE_CORPUS = {
 _meta:{
  title:"Schneider Electric Industrial Engineering Corpus",
  built:"CANON PS2 · structured from public product knowledge",
  disclaimer:"Families/software/protocols = VERIFIED public knowledge. Exact refs/URLs/counts → VERIFY on se.com. CANON demo + mapping rules = PROPOSED. No live crawl performed.",
  legend:{VERIFIED:"Established public product fact",INFERRED:"Derived from verified facts",PROPOSED:"CANON demo/architecture concept",VERIFY:"Plausible but confirm on official source",ROADMAP:"Future CANON capability"}
 },

 families:[
  {id:"modicon",name:"Modicon",category:"Controllers · PLC / PAC",examples:["M221","M241","M251","M262","M340","M580","M580 Safety","Momentum","Quantum (legacy)","Premium (legacy)"],software:["EcoStruxure Machine Expert","EcoStruxure Control Expert"],comm:["Modbus","EtherNet/IP","OPC UA","CANopen"],domains:["Machine","Process","Safety"],truth:"VERIFIED"},
  {id:"harmony",name:"Harmony",category:"HMI · Panels & Control",examples:["Harmony GTU","Harmony GTUX","Harmony ST6","Harmony STM6","Harmony STO","Harmony STU","Harmony P6","XVU Signal Tower","pushbuttons / pilot lights"],software:["EcoStruxure Operator Terminal Expert","Vijeo Designer"],comm:["Modbus","EtherNet/IP","OPC UA"],domains:["Operator interface","Signalling"],truth:"VERIFIED"},
  {id:"altivar",name:"Altivar",category:"Drives · VFD",examples:["ATV320 (Machine)","ATV340 (Machine HP)","ATV630/650 (Process)","ATV930/950 (Process HP)","ATV212 (HVAC)","ATV6000 (MV)"],software:["EcoStruxure Machine Expert","SoMove"],comm:["Modbus","EtherNet/IP","CANopen","PROFINET (opt)"],domains:["Motor speed control"],truth:"VERIFIED"},
  {id:"lexium",name:"Lexium",category:"Motion · Servo",examples:["Lexium 28","Lexium 32","Lexium 62 (multi-axis)","Lexium ILA/ILE (integrated)","BMH/BSH servo motors"],software:["EcoStruxure Machine Expert - Motion"],comm:["Modbus","CANopen","Sercos","Pulse/dir"],domains:["Motion / positioning"],truth:"VERIFIED"},
  {id:"pacdrive",name:"PacDrive",category:"Motion · Automation Controllers",examples:["PacDrive LMC (Eco/Pro/Pro2)","multi-axis motion"],software:["EcoStruxure Machine Expert"],comm:["Sercos","EtherNet/IP","OPC UA"],domains:["High-performance motion / robotics"],truth:"VERIFIED"},
  {id:"tesys",name:"TeSys",category:"Motor control & management",examples:["TeSys D/F/B contactors","TeSys island","TeSys T motor management","TeSys U / Giga","Altistart soft starters"],software:["EcoStruxure Machine Expert","DTM/FDT"],comm:["EtherNet/IP","Modbus","PROFINET","IO-Link"],domains:["Motor starting & protection"],truth:"VERIFIED"},
  {id:"io",name:"Modicon I/O",category:"I/O modules",examples:["Modicon X80 (M340/M580)","TM3 (M221/M241/M251)","TM5 / TM7 (distributed)","Momentum I/O"],software:["EcoStruxure Machine Expert","EcoStruxure Control Expert"],comm:["backplane","EtherNet/IP","Modbus"],domains:["DI/DO/AI/AO · expert · safety"],truth:"VERIFIED"},
  {id:"powerlogic",name:"PowerLogic",category:"Metering & power quality",examples:["PM8000","PM5000","ION9000","Acti9 iEM"],software:["EcoStruxure Power Monitoring Expert"],comm:["Modbus TCP","IEC 61850 (opt)"],domains:["Energy · power quality"],truth:"VERIFIED"},
  {id:"zelio",name:"Zelio Logic",category:"Smart relay",examples:["Zelio Logic SR2/SR3"],software:["Zelio Soft"],comm:["Modbus (opt)"],domains:["Simple logic"],truth:"VERIFIED"},
  {id:"preventa",name:"Preventa",category:"Machine safety",examples:["Preventa safety relays","XPS controllers","safety I/O","e-stop / guard switches / light curtains"],software:["EcoStruxure Machine Expert - Safety"],comm:["safety I/O","EtherNet/IP CIP Safety"],domains:["Functional safety"],truth:"VERIFIED"},
 ],

 controllers:[
  {name:"M221",role:"Compact machine logic controller",comm:["Modbus","Ethernet (variant)"],software:"EcoStruxure Machine Expert - Basic",motion:"limited",safety:"no",status:"current",truth:"VERIFIED"},
  {name:"M241",role:"Machine logic controller",comm:["Modbus","Ethernet","CANopen","serial"],software:"EcoStruxure Machine Expert",motion:"basic",safety:"no",status:"current",truth:"VERIFIED"},
  {name:"M251",role:"Machine logic controller (Ethernet)",comm:["Ethernet","Modbus"],software:"EcoStruxure Machine Expert",motion:"basic",safety:"no",status:"current",truth:"VERIFIED"},
  {name:"M262",role:"Machine + motion controller",comm:["Ethernet","OPC UA","TSN","CANopen"],software:"EcoStruxure Machine Expert",motion:"yes (Logic/Motion)",safety:"no",status:"current",truth:"VERIFIED"},
  {name:"M340",role:"Mid-range PAC (process/machine)",comm:["Modbus","Ethernet","CANopen"],software:"EcoStruxure Control Expert",motion:"module",safety:"no",status:"current",truth:"VERIFIED"},
  {name:"M580",role:"ePAC — Ethernet backplane PAC",comm:["Modbus TCP","EtherNet/IP","OPC UA (embedded)"],software:"EcoStruxure Control Expert",motion:"module",safety:"no",status:"current",truth:"VERIFIED"},
  {name:"M580 Safety",role:"Safety PAC",comm:["Modbus TCP","EtherNet/IP","OPC UA"],software:"EcoStruxure Control Expert (Safety)",motion:"no",safety:"SIL3 (verify)",status:"current",truth:"VERIFIED"},
  {name:"Momentum / Quantum / Premium",role:"Legacy controllers",comm:["Modbus","Ethernet"],software:"Unity Pro / Control Expert",motion:"varies",safety:"varies",status:"legacy",truth:"VERIFIED"},
 ],

 software:[
  {name:"EcoStruxure Machine Expert",purpose:"Machine PLC/motion engineering (Somachine successor)",phase:"build",targets:["M241","M251","M262","PacDrive","Altivar"],hmi:"integrated / EOTE",truth:"VERIFIED"},
  {name:"EcoStruxure Machine Expert - Basic",purpose:"Programming for M221",phase:"build",targets:["M221"],hmi:"—",truth:"VERIFIED"},
  {name:"EcoStruxure Control Expert",purpose:"Process/PAC engineering (Unity Pro successor)",phase:"build",targets:["M340","M580","Quantum"],hmi:"—",truth:"VERIFIED"},
  {name:"EcoStruxure Automation Expert",purpose:"Universal automation · IEC 61499 · Soft dPAC",phase:"build+runtime",targets:["Modicon","Soft dPAC"],hmi:"integrated",truth:"VERIFIED"},
  {name:"EcoStruxure Operator Terminal Expert (EOTE)",purpose:"HMI configuration for Harmony panels; large built-in object/template library",phase:"build",targets:["Harmony GTU/ST6/STU"],hmi:"native",note:"'650+ objects' figure → VERIFY on se.com",truth:"VERIFIED"},
  {name:"Vijeo Designer",purpose:"Legacy HMI configuration (Magelis/Harmony)",phase:"build",targets:["Harmony/Magelis"],hmi:"native",truth:"VERIFIED"},
  {name:"EcoStruxure Machine SCADA Expert",purpose:"Machine-edition SCADA/HMI runtime",phase:"build+runtime",targets:["PC/edge"],hmi:"native",truth:"VERIFIED"},
  {name:"EcoStruxure Process Expert",purpose:"Hybrid DCS engineering",phase:"build+runtime",targets:["M580","process"],hmi:"native",truth:"VERIFIED"},
  {name:"EcoStruxure OPC UA Server Expert",purpose:"OPC UA server for Schneider controllers",phase:"runtime",targets:["Modicon"],hmi:"—",truth:"VERIFIED"},
  {name:"SoMove",purpose:"Drive commissioning (Altivar/Lexium)",phase:"build",targets:["Altivar","Lexium"],hmi:"—",truth:"VERIFIED"},
 ],

 hmi:[
  {name:"Harmony GTU / GTUX",kind:"Modular HMI (box + display)",runtime:"EOTE / Vijeo",comm:["Modbus","EtherNet/IP","OPC UA"],truth:"VERIFIED"},
  {name:"Harmony ST6 / STM6",kind:"Advanced panel HMI",runtime:"EOTE / Vijeo",comm:["Modbus","EtherNet/IP","OPC UA"],truth:"VERIFIED"},
  {name:"Harmony STO / STU",kind:"Optimised/base panel HMI",runtime:"Vijeo / EOTE",comm:["Modbus","Ethernet"],truth:"VERIFIED"},
  {name:"Harmony P6",kind:"Industrial panel PC",runtime:"SCADA/EOTE",comm:["Ethernet","OPC UA"],truth:"VERIFIED"},
  {name:"Magelis (brand → Harmony)",kind:"Legacy HMI branding",runtime:"Vijeo",comm:["Modbus"],truth:"VERIFIED"},
 ],

 standards:[
  {id:"ISA-101",name:"ISA-101 HMI",relevance:"HMI design philosophy — grey normal, colour for abnormal; hierarchy",canon:"informed by",truth:"VERIFIED"},
  {id:"ISA-18.2",name:"ISA-18.2 / IEC 62682",relevance:"Alarm management lifecycle, priority, shelving",canon:"informed by",truth:"VERIFIED"},
  {id:"IEC-61131",name:"IEC 61131-3",relevance:"PLC programming languages",canon:"context",truth:"VERIFIED"},
  {id:"IEC-61499",name:"IEC 61499",relevance:"Distributed automation (EcoStruxure Automation Expert)",canon:"context",truth:"VERIFIED"},
  {id:"OPCUA",name:"OPC UA (IEC 62541)",relevance:"Information model & secure transport for machine context",canon:"ingestion target",truth:"VERIFIED"},
  {id:"PackML",name:"PackML / OMAC",relevance:"Machine state model (states, modes)",canon:"informed by",truth:"VERIFIED"},
  {id:"MTP",name:"MTP (VDI/VDE/NAMUR 2658)",relevance:"Module Type Package — modular process HMI/services",canon:"inspired by",truth:"VERIFIED"},
  {id:"AML",name:"AutomationML (IEC 62714)",relevance:"Engineering data exchange (topology/roles)",canon:"ingestion (roadmap)",truth:"VERIFIED"},
  {id:"AAS",name:"Asset Administration Shell (IEC 63278)",relevance:"Digital twin/asset metadata (no HMI submodel yet)",canon:"ingestion (roadmap)",truth:"VERIFIED"},
  {id:"EEMUA",name:"EEMUA 191",relevance:"Alarm systems guidance",canon:"informed by",truth:"VERIFIED"},
 ],

 // Generic (not Schneider-specific) machine structure CANON normalises to:
 hierarchy:["PLANT","AREA","LINE","MACHINE","UNIT","ASSET","DEVICE","SIGNAL","COMMAND","PERMISSIVE","ALARM","HMI VIEW"],

 // CANON semantic → HMI component mapping (CANON rules, not a Schneider spec)
 mapping:[
  {sem:"Pressure",hmi:"gauge · engineering range · trend · HI/LO alarm",truth:"PROPOSED"},
  {sem:"Level",hmi:"tank level · value tile · HI/LO alarm",truth:"PROPOSED"},
  {sem:"Flow / Temp",hmi:"analog value tile · trend",truth:"PROPOSED"},
  {sem:"Pump / Motor",hmi:"symbol · run state badge · START/STOP (permissive-gated)",truth:"PROPOSED"},
  {sem:"Valve",hmi:"symbol · OPEN/CLOSED state · OPEN command",truth:"PROPOSED"},
  {sem:"Machine state",hmi:"signal tower (XVU) · state banner",truth:"PROPOSED"},
  {sem:"Alarm",hmi:"alarm banner / list (ISA-18.2-informed)",truth:"PROPOSED"},
 ],

 // Current vs roadmap for CANON's own ingestion capabilities
 capability:[
  {cap:"Canonical model (typed signals/commands/alarms)",status:"CURRENT"},
  {cap:"Intent → validated dynamic HMI",status:"CURRENT"},
  {cap:"PLC-authoritative control (permissive gate)",status:"CURRENT"},
  {cap:"Change impact → regenerate → baseline",status:"CURRENT"},
  {cap:"Real recorded data replay (SKAB)",status:"CURRENT"},
  {cap:"Schneider register-map catalog (typical)",status:"CURRENT"},
  {cap:"Local model fine-tune (CANON brain)",status:"CURRENT"},
  {cap:"OPC UA nodeset ingestion (M580 embedded server)",status:"ROADMAP"},
  {cap:"AutomationML / MTP / AAS import",status:"ROADMAP"},
  {cap:"Export → EcoStruxure Operator Terminal Expert project",status:"ROADMAP"},
  {cap:"Live Modbus/OPC UA poll to physical device",status:"ROADMAP"},
 ],
};
