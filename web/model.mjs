export function number(value,label,{max=10_000_000,blank=false}={}) {
 if(value==null||String(value).trim()===''){if(blank)return 0;throw new Error(`${label} is required; enter 0 if none.`);}
 if(!['number','string'].includes(typeof value))throw new Error(`${label} must be a number.`);
 const n=Number(value);if(!Number.isFinite(n)||n<0||n>max)throw new Error(`${label} must be between 0 and ${max.toLocaleString('en-CA')}.`);return n;
}
export function annualPay(scenario) {
 const pay=number(scenario.pay,'Pay'),hours=number(scenario.hours,'Work hours',{max:168}),weeks=number(scenario.weeks,'Paid weeks',{max:52.18});
 if(!['annual','hourly'].includes(scenario.payPeriod))throw new Error('Invalid pay period.');
 if(scenario.payPeriod==='hourly'&&pay>0&&(hours===0||weeks===0))throw new Error('Hourly pay requires positive paid hours and weeks.');
 return scenario.payPeriod==='annual'?pay:pay*hours*weeks;
}
export function evaluate(scenario,categories) {
 const pay=annualPay(scenario),costs=Object.fromEntries(categories.map(c=>[c.id,number(scenario.costs?.[c.id],c.label)]));
 const monthlyCosts=Object.values(costs).reduce((a,b)=>a+b,0),hours=number(scenario.hours,'Work hours',{max:168}),weeks=number(scenario.weeks,'Paid weeks',{max:52.18}),commuteHours=number(scenario.commuteHours,'Commute hours',{max:168});
 if(hours+commuteHours>168)throw new Error('Work and commuting hours cannot exceed the hours in a week.');
 const committedHours=(hours+commuteHours)*weeks;
 return {annualPay:pay,monthlyPay:pay/12,monthlyCosts,costs,beforeDeductions:pay/12-monthlyCosts,committedHours,payPerCommittedHour:committedHours>0?pay/committedHours:null};
}
export function compareMove(state,categories) {
 const current=evaluate(state.current,categories),proposed=evaluate(state.proposed,categories),moving=number(state.moving,'One-time moving cost'),horizon=number(state.horizon,'Comparison horizon',{max:600});
 if(horizon<1||!Number.isInteger(horizon))throw new Error('Choose a whole number of months from 1 to 600.');
 const costDifference=proposed.monthlyCosts-current.monthlyCosts,payDifference=proposed.monthlyPay-current.monthlyPay,difference=payDifference-costDifference;
 const rawEquivalentSalary=current.annualPay+costDifference*12;
 const equivalentSalary=Math.max(0,rawEquivalentSalary);
 return {current,proposed,moving,horizon,costDifference,payDifference,difference,equivalentSalary,equivalentSalaryWithMove:Math.max(0,rawEquivalentSalary+moving*12/horizon),overHorizon:difference*horizon-moving,recoveryMonths:moving===0?0:difference>0?Math.ceil(moving/difference):null};
}
export function validateScenario(value,categories) {
 if(!value||value.schema_version!==1||value.tool!=='movebench')throw new Error('This is not a Move Bench scenario.');
 for(const side of ['current','proposed']) {const s=value[side];if(!s||typeof s.place!=='string'||s.place.length>120)throw new Error('Invalid place label.');if(typeof s.region!=='string'||s.region.length>120)throw new Error('Invalid reference region.');}
 compareMove(value,categories);return value;
}
export function csvCell(value){return '"'+(typeof value==='string' && /^[=+\-@]/.test(value) ? "'"+value : String(value??'')).replaceAll('"','""')+'"';}

export function applyPlacePair(state,pair) {
 if(!state||!pair)throw new Error('Choose a valid place pair.');
 for(const side of ['current','proposed'])for(const key of ['place','region'])if(typeof pair[side]?.[key]!=='string'||!pair[side][key].trim()||pair[side][key].length>120)throw new Error('Invalid place pair.');
 return {...state,current:{...state.current,place:pair.current.place,region:pair.current.region},proposed:{...state.proposed,place:pair.proposed.place,region:pair.proposed.region}};
}
