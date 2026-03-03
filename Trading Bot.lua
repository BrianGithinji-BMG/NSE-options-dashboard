//@version=6
strategy("VALD Strategy Bot", overlay=true, initial_capital=10000, default_qty_type=strategy.percent_of_equity, default_qty_value=0.5, commission_type=strategy.commission.percent, commission_value=0.02)

// ============================================================================
// VALD STRATEGY - AUTOMATED TRADING BOT
// Volatility-Adjusted Liquidity Displacement Strategy
// ============================================================================

// ===========================
// USER INPUTS
// ===========================

// Risk Management
riskPercent = input.float(0.5, title="Risk Per Trade (%)", minval=0.1, maxval=2.0, step=0.1) / 100
maxDailyLosses = input.int(3, title="Max Losses Per Day", minval=1, maxval=5)

// ATR Settings
atrPeriod = input.int(14, title="ATR Period", minval=5, maxval=50)
atrMinimum = input.float(4.50, title="ATR Minimum Threshold", minval=0.5, step=0.5)
atrMultiplier = input.float(0.3, title="ATR Stop Loss Multiplier", minval=0.1, maxval=1.0, step=0.1)

// Liquidity Pool Settings
liquidityTouches = input.int(3, title="Min Liquidity Pool Touches", minval=2, maxval=5)
liquidityPipTolerance = input.float(8.0, title="Liquidity Pip Tolerance", minval=3.0, maxval=15.0, step=1.0)
minBarsForZone = input.int(24, title="Min Bars for Zone Formation", minval=10, maxval=50)

// Sweep & Displacement Settings
sweepPips = input.float(5.0, title="Sweep Breakout Pips", minval=3.0, maxval=10.0, step=0.5)
displacementPips = input.float(12.0, title="Displacement Move Pips", minval=8.0, maxval=20.0, step=1.0)
volumeMultiplier = input.float(1.5, title="Volume Spike Multiplier", minval=1.2, maxval=2.0, step=0.1)

// Take Profit Ratios
tp1Ratio = input.float(1.5, title="TP1 R:R Ratio", minval=1.0, maxval=3.0, step=0.1)
tp2Ratio = input.float(2.5, title="TP2 R:R Ratio", minval=1.5, maxval=4.0, step=0.1)
tp3Ratio = input.float(3.5, title="TP3 R:R Ratio", minval=2.0, maxval=5.0, step=0.1)

// Session Filters (in UTC/GMT)
londonStart = input.int(8, title="London Session Start (GMT)", minval=0, maxval=23)
londonEnd = input.int(12, title="London Session End (GMT)", minval=0, maxval=23)
nyStart = input.int(13, title="NY Session Start (GMT)", minval=0, maxval=23)
nyEnd = input.int(17, title="NY Session End (GMT)", minval=0, maxval=23)

// Visual Settings
showZones = input.bool(true, title="Show Liquidity Zones")
showSignals = input.bool(true, title="Show Entry Signals")
showLabels = input.bool(true, title="Show Signal Labels")

// ===========================
// CALCULATIONS
// ===========================

// ATR Calculation
atrValue = ta.atr(atrPeriod)
atrSma = ta.sma(atrValue, 20)
atrExpanding = atrValue > atrValue[10] and atrValue > atrSma and atrValue > atrMinimum

// Volume Filter
volumeSma = ta.sma(volume, 20)
volumeSpike = volume > volumeSma * volumeMultiplier

// Session Filter
currentHour = hour(time)
inLondonSession = currentHour >= londonStart and currentHour < londonEnd
inNYSession = currentHour >= nyStart and currentHour < nyEnd
inTradingSession = inLondonSession or inNYSession

// Avoid first 30 minutes of session
currentMinute = minute(time)
earlySession = (currentHour == londonStart and currentMinute < 30) or (currentHour == nyStart and currentMinute < 30)

// VWAP Calculation
vwapValue = ta.vwap(close)

// Swing High/Low Detection
swingPeriod                  = 5
swingHigh = ta.pivothigh(high, swingPeriod, swingPeriod)
swingLow = ta.pivotlow(low, swingPeriod, swingPeriod)

// ===========================
// LIQUIDITY ZONE DETECTION
// ===========================

// Variables to store liquidity zones
var float liquidityLowZone = na
var float liquidityHighZone = na
var int lowTouchCount = 0
var int highTouchCount = 0
var int barsInLowZone = 0
var int barsInHighZone = 0

// Detect Equal Lows (support liquidity)
if not na(swingLow)
    if na(liquidityLowZone)
        liquidityLowZone := swingLow
        lowTouchCount := 1
        barsInLowZone := 0
    else if math.abs(swingLow - liquidityLowZone) <= liquidityPipTolerance * 0.0001
        lowTouchCount += 1
        barsInLowZone += 1
    else if swingLow < liquidityLowZone
        liquidityLowZone := swingLow
        lowTouchCount := 1
        barsInLowZone := 0

// Detect Equal Highs (resistance liquidity)
if not na(swingHigh)
    if na(liquidityHighZone)
        liquidityHighZone := swingHigh
        highTouchCount := 1
        barsInHighZone := 0
    else if math.abs(swingHigh - liquidityHighZone) <= liquidityPipTolerance * 0.0001
        highTouchCount += 1
        barsInHighZone += 1
    else if swingHigh > liquidityHighZone
        liquidityHighZone := swingHigh
        highTouchCount := 1
        barsInHighZone := 0

// Increment bars in zone
barsInLowZone += 1
barsInHighZone += 1

// Valid liquidity zones
validLowZone = lowTouchCount >= liquidityTouches and barsInLowZone >= minBarsForZone
validHighZone = highTouchCount >= liquidityTouches and barsInHighZone >= minBarsForZone

// ===========================
// SWEEP DETECTION
// ===========================

// Calculate range SMA once per bar to avoid conditional execution issues
rangeSma = ta.sma(high - low, 20)

// Long Setup: Sweep below equal lows
sweepBelow = validLowZone and low <= liquidityLowZone - (sweepPips * 0.0001) and close >= liquidityLowZone - (3 * 0.0001)
sweepBelowWithVolume = sweepBelow and volumeSpike
longSweepCandle = sweepBelowWithVolume and (high - low) > rangeSma * 1.5

// Short Setup: Sweep above equal highs  
sweepAbove = validHighZone and high >= liquidityHighZone + (sweepPips * 0.0001) and close <= liquidityHighZone + (3 * 0.0001)
sweepAboveWithVolume = sweepAbove and volumeSpike
shortSweepCandle = sweepAboveWithVolume and (high - low) > rangeSma * 1.5

// Store sweep candle lows/highs
var float sweepCandleLow = na
var float sweepCandleHigh = na
var int barsSinceSweep = 0

if longSweepCandle
    sweepCandleLow := low
    barsSinceSweep := 0
    
if shortSweepCandle
    sweepCandleHigh := high
    barsSinceSweep := 0
    
barsSinceSweep += 1

// ===========================
// DISPLACEMENT & CONFIRMATION
// ===========================

// Long Displacement: Strong bullish candle after sweep
longDisplacement = not na(sweepCandleLow) and barsSinceSweep <= 5 and 
                   close > open and 
                   close > high[1] + (displacementPips * 0.0001) and
                   (close - low) / (high - low) >= 0.70 and
                   volumeSpike

// Structure break: Close above recent swing high
recentSwingHigh = not na(swingHigh) ? high : high
longStructureBreak = close > recentSwingHigh

// VWAP confirmation
longVwapOk = close > vwapValue or math.abs(close - vwapValue) <= 5 * 0.0001

// Final Long Signal
longSignal = longDisplacement and longStructureBreak and longVwapOk and atrExpanding and inTradingSession and not earlySession

// Short Displacement: Strong bearish candle after sweep
shortDisplacement = (not na(sweepCandleHigh) and barsSinceSweep <= 5 and 
                    close < open and 
                    close < low[1] - (displacementPips * 0.0001) and 
                    (high - close) / (high - low) >= 0.70 and 
                    volumeSpike
    )
// Structure break: Close below recent swing low
recentSwingLow = not na(swingLow) ? low : low
shortStructureBreak = close < recentSwingLow

// VWAP confirmation
shortVwapOk = close < vwapValue or math.abs(close - vwapValue) <= 5 * 0.0001

// Final Short Signal
shortSignal = shortDisplacement and shortStructureBreak and shortVwapOk and atrExpanding and inTradingSession and not earlySession

// ===========================
// POSITION SIZING & RISK MANAGEMENT
// ===========================

// Calculate stop distances
longStopDistance = close - (sweepCandleLow - atrValue * atrMultiplier - 2 * 0.0001)
shortStopDistance = (sweepCandleHigh + atrValue * atrMultiplier + 2 * 0.0001) - close

// Ensure minimum/maximum stop distances
minStopPips = 8 * 0.0001
maxStopPips = atrValue * 1.5

longStopDistance := math.max(longStopDistance, minStopPips)
longStopDistance := math.min(longStopDistance, maxStopPips)
shortStopDistance := math.max(shortStopDistance, minStopPips)
shortStopDistance := math.min(shortStopDistance, maxStopPips)

// Calculate Take Profit levels
longTP1 = close + longStopDistance * tp1Ratio
longTP2 = close + longStopDistance * tp2Ratio  
longTP3 = close + longStopDistance * tp3Ratio

shortTP1 = close - shortStopDistance * tp1Ratio
shortTP2 = close - shortStopDistance * tp2Ratio
shortTP3 = close - shortStopDistance * tp3Ratio

// ===========================
// DAILY LOSS LIMIT
// ===========================

var int dailyLosses = 0
var int lastLossDay = 0

// Reset counter at start of new day
if dayofweek != dayofweek[1]
    dailyLosses := 0
    lastLossDay := 0

// Track losses (reset on new day)
if dayofmonth != dayofmonth[1]
    dailyLosses := 0

// Don't trade if daily loss limit hit
dailyLossLimitHit = dailyLosses >= maxDailyLosses

// ===========================
// STRATEGY EXECUTION
// ===========================

// Entry Conditions
longEntry = longSignal and strategy.position_size == 0 and not dailyLossLimitHit
shortEntry = shortSignal and strategy.position_size == 0 and not dailyLossLimitHit

// Execute Long Trades
if longEntry
    longStop = sweepCandleLow - atrValue * atrMultiplier - 2 * 0.0001 * close
    strategy.entry("Long", strategy.long, comment="LONG SWEEP")
    strategy.exit("TP1", "Long", limit=longTP1, stop=longStop, qty_percent=33)
    strategy.exit("TP2", "Long", limit=longTP2, stop=longStop, qty_percent=33)
    strategy.exit("TP3", "Long", limit=longTP3, stop=longStop, qty_percent=34)

// Execute Short Trades  
if shortEntry
    shortStop = sweepCandleHigh + atrValue * atrMultiplier + 2 * 0.0001 * close
    strategy.entry("Short", strategy.short, comment="SHORT SWEEP")
    strategy.exit("TP1", "Short", limit=shortTP1, stop=shortStop, qty_percent=33)
    strategy.exit("TP2", "Short", limit=shortTP2, stop=shortStop, qty_percent=33)
    strategy.exit("TP3", "Short", limit=shortTP3, stop=shortStop, qty_percent=34)

// Breakeven and exit management is handled by the TP exit orders above

// ===========================
// VISUALIZATION
// ===========================

// Plot Liquidity Zones
plot(showZones and validLowZone ? liquidityLowZone : na, title="Support Liquidity", color=color.new(color.green, 50), linewidth=2, style=plot.style_circles)
plot(showZones and validHighZone ? liquidityHighZone : na, title="Resistance Liquidity", color=color.new(color.red, 50), linewidth=2, style=plot.style_circles)

// Plot VWAP
plot(vwapValue, title="VWAP", color=color.new(color.orange, 30), linewidth=2)

// Plot ATR Expanding Indicator
bgcolor(atrExpanding ? color.new(color.blue, 95) : na, title="ATR Expanding")

// Plot Entry Signals
plotshape(showSignals and longEntry, title="Long Signal", location=location.belowbar, color=color.new(color.green, 0), style=shape.triangleup, size=size.small)
plotshape(showSignals and shortEntry, title="Short Signal", location=location.abovebar, color=color.new(color.red, 0), style=shape.triangledown, size=size.small)

// Labels with Trade Info
if showLabels and longEntry
    label.new(bar_index, low, text="LONG\nATR:" + str.tostring(atrValue, "#.##") + "\nStop:" + str.tostring(longStopDistance * 10000, "#.#") + "p", 
              style=label.style_label_up, color=color.new(color.green, 20), textcolor=color.white, size=size.small)

if showLabels and shortEntry  
    label.new(bar_index, high, text="SHORT\nATR:" + str.tostring(atrValue, "#.##") + "\nStop:" + str.tostring(shortStopDistance * 10000, "#.#") + "p",
              style=label.style_label_down, color=color.new(color.red, 20), textcolor=color.white, size=size.small)

// Plot Daily Loss Limit Warning
bgcolor(dailyLossLimitHit ? color.new(color.red, 80) : na, title="Daily Loss Limit Hit")

// ===========================
// PERFORMANCE METRICS (shown in strategy tester)
// ===========================

// These are automatically calculated by Pine Script strategy tester:
// - Total Trades
// - Win Rate %
// - Profit Factor
// - Average Trade
// - Max Drawdown
// - Sharpe Ratio
// etc.