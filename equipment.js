/* CANON — Schneider Electric equipment catalog.
   Real device families with representative signal/register maps so the canonical
   model can be built from actual Schneider gear (Modicon, Altivar, PowerLogic, TeSys, Lexium).
   NOTE: Modbus/register addresses are TYPICAL values from the device communication
   manuals; verify against your specific model + firmware. Marked per device. */
window.SE_EQUIP = [
 {
  id:"se:m241", brand:"Schneider Electric", family:"Modicon", model:"M241 (TM241CE24T)",
  kind:"Logic Controller", proto:"Modbus TCP / EtherNet-IP / Machine Expert",
  role:"Hosts the canonical control logic; CANON binds HMI to its symbolic variables.",
  note:"Symbolic variables via EcoStruxure Machine Expert; addresses map to %MW/%M/%Q/%I.",
  signals:[
   {name:"P401_RUN_FB",desc:"Pump run feedback",io:"DI",addr:"%I0.1"},
   {name:"XV401_OPEN_FB",desc:"Valve open feedback",io:"DI",addr:"%I0.2"},
   {name:"P401_START_CMD",desc:"Pump start cmd",io:"DO",addr:"%Q0.1"},
   {name:"LT401",desc:"Tank level",io:"AI",unit:"%",min:0,max:100,addr:"%MW20"},
  ],
 },
 {
  id:"se:m580", brand:"Schneider Electric", family:"Modicon", model:"M580 ePAC (BMEP582040)",
  kind:"Process Automation Controller", proto:"Modbus TCP / OPC UA (embedded) / EtherNet-IP",
  role:"Process PAC with embedded OPC UA server — ideal source for CANON's information model.",
  note:"Exposes an OPC UA server; CANON can ingest its address space directly.",
  signals:[
   {name:"PT401",desc:"Discharge pressure",io:"AI",unit:"bar",min:0,max:10,addr:"OPCUA:TK401.PT401"},
   {name:"FT401",desc:"Discharge flow",io:"AI",unit:"m³/h",min:0,max:120,addr:"OPCUA:TK401.FT401"},
   {name:"TT401",desc:"Fluid temperature",io:"AI",unit:"°C",min:0,max:150,addr:"OPCUA:TK401.TT401"},
  ],
 },
 {
  id:"se:atv630", brand:"Schneider Electric", family:"Altivar", model:"ATV630 (Process VFD)",
  kind:"Variable Frequency Drive", proto:"Modbus TCP / Modbus RTU (CANopen, PROFINET opt.)",
  role:"Drives the pump motor; CANON generates a drive faceplate from its parameter map.",
  note:"Modbus register/parameter addresses per Altivar Process communication manual — verify vs firmware.",
  signals:[
   {name:"ETA",desc:"Status word",io:"R",addr:"3201"},
   {name:"RFRD",desc:"Output frequency (0.1 Hz)",io:"AI",unit:"Hz",min:0,max:60,addr:"8604"},
   {name:"LCR",desc:"Motor current (0.1 A)",io:"AI",unit:"A",min:0,max:150,addr:"3204"},
   {name:"OPR",desc:"Output power (%)",io:"AI",unit:"%",min:0,max:150,addr:"3211"},
   {name:"LFT",desc:"Last fault code",io:"R",addr:"7121"},
  ],
  commands:[
   {name:"CMD",desc:"Command word (run/stop/reset)",addr:"8501"},
   {name:"LFRD",desc:"Frequency setpoint (0.1 Hz)",addr:"8602"},
   {name:"ACC",desc:"Acceleration ramp",addr:"9001"},{name:"DEC",desc:"Deceleration ramp",addr:"9002"},
  ],
 },
 {
  id:"se:atv320", brand:"Schneider Electric", family:"Altivar", model:"ATV320 (Machine VFD)",
  kind:"Variable Frequency Drive", proto:"Modbus RTU/TCP · CANopen",
  role:"Compact machine drive; same CANON drive-faceplate template, different register map.",
  note:"Addresses per ATV320 Modbus manual — verify vs firmware.",
  signals:[
   {name:"ETA",desc:"Status word",io:"R",addr:"3201"},
   {name:"RFRD",desc:"Output frequency (0.1 Hz)",io:"AI",unit:"Hz",min:0,max:60,addr:"8604"},
   {name:"LCR",desc:"Motor current (0.1 A)",io:"AI",unit:"A",min:0,max:60,addr:"3204"},
  ],
  commands:[{name:"CMD",desc:"Command word",addr:"8501"},{name:"LFRD",desc:"Freq setpoint",addr:"8602"}],
 },
 {
  id:"se:pm8000", brand:"Schneider Electric", family:"PowerLogic", model:"PM8000",
  kind:"Power & Energy Meter", proto:"Modbus TCP · IEC 61850 (opt.)",
  role:"Energy/power quality metering; CANON generates an energy dashboard faceplate.",
  note:"32-bit float registers per PowerLogic PM8000 Modbus map — typical, verify vs model.",
  signals:[
   {name:"I_avg",desc:"Current average",io:"AI",unit:"A",min:0,max:1000,addr:"3000"},
   {name:"Vll_avg",desc:"Voltage L-L average",io:"AI",unit:"V",min:0,max:600,addr:"3026"},
   {name:"P_total",desc:"Active power total",io:"AI",unit:"kW",min:0,max:2000,addr:"3060"},
   {name:"PF_total",desc:"Power factor total",io:"AI",unit:"",min:-1,max:1,addr:"3084"},
   {name:"Freq",desc:"Frequency",io:"AI",unit:"Hz",min:45,max:65,addr:"3110"},
   {name:"E_active",desc:"Active energy delivered",io:"AI",unit:"kWh",min:0,max:1e9,addr:"3204"},
  ],
 },
 {
  id:"se:tesys", brand:"Schneider Electric", family:"TeSys", model:"TeSys island",
  kind:"Motor Management / Load Management", proto:"EtherNet-IP / PROFINET / Modbus TCP",
  role:"Digital load management for motor starters; CANON generates a motor-group overview.",
  note:"Avatar-based data model; addresses via TeSys island DTM / device catalog.",
  signals:[
   {name:"M1_RUN",desc:"Starter 1 running",io:"DI",addr:"AVATAR:Starter1.Run"},
   {name:"M1_I",desc:"Starter 1 current",io:"AI",unit:"A",min:0,max:100,addr:"AVATAR:Starter1.Current"},
   {name:"M1_TRIP",desc:"Starter 1 thermal trip",io:"DI",addr:"AVATAR:Starter1.Trip"},
  ],
 },
 {
  id:"se:lexium28", brand:"Schneider Electric", family:"Lexium", model:"Lexium 28 (LXM28)",
  kind:"Servo Drive", proto:"Modbus / CANopen / Pulse-train",
  role:"Motion axis; CANON generates an axis faceplate (position/velocity/torque).",
  note:"Object addresses per LXM28 manual — verify vs firmware.",
  signals:[
   {name:"P_act",desc:"Actual position",io:"AI",unit:"inc",min:-1e6,max:1e6,addr:"LXM:Pos"},
   {name:"V_act",desc:"Actual velocity",io:"AI",unit:"rpm",min:-3000,max:3000,addr:"LXM:Vel"},
   {name:"Trq",desc:"Actual torque",io:"AI",unit:"%",min:-300,max:300,addr:"LXM:Trq"},
  ],
 },
 {
  id:"se:xvu", brand:"Schneider Electric", family:"Harmony", model:"XVU Signal Tower",
  kind:"Stack Light / Tower Lamp", proto:"Discrete DO (24 V) / IO-Link variant",
  role:"Machine-state signalling — CANON drives it from validated machine state (run / warning / alarm).",
  note:"Lamp outputs are plain DOs; IO-Link variants report diagnostics.",
  signals:[
   {name:"XVU_GRN",desc:"Green lamp · running / normal",io:"DO",addr:"%Q1.1"},
   {name:"XVU_AMB",desc:"Amber lamp · warning / anomaly",io:"DO",addr:"%Q1.2"},
   {name:"XVU_RED",desc:"Red lamp · active alarm",io:"DO",addr:"%Q1.3"},
  ],
 },
 {
  id:"se:harmony", brand:"Schneider Electric", family:"Harmony", model:"Harmony GTU / Magelis",
  kind:"HMI Panel (render target)", proto:"Vijeo Designer / EcoStruxure Operator Terminal Expert",
  role:"The physical panel CANON's generated HMI is designed to render on.",
  note:"CANON output is aligned to ISA-101; export adapter to Vijeo/EOTE is roadmap.",
  signals:[],
 },
];
