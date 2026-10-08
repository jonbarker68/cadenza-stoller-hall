pragma Singleton
import QtQuick

QtObject {
    // Reference canvas. Slide.qml scales these nominal values to the
    // actual display using its existing scaleUnit calculation.
    readonly property real referenceWidth: 1280
    readonly property real referenceHeight: 720

    // Audience palette
    readonly property color background: "#101922"
    readonly property color accent: "#d9b679"
    readonly property color titleText: "#f5f1e8"
    readonly property color bodyText: "#becad1"
    readonly property color timerTrack: "#2b3945"

    // Main slide layout
    readonly property real sideMargin: 70
    readonly property real topRuleHeight: 5
    readonly property real headerY: 48
    readonly property real contentY: 158
    readonly property real contentSpacing: 18

    // Main slide typography
    readonly property real headerFontPx: 18
    readonly property real headerLetterSpacing: 3
    readonly property real titleFontPx: 48
    readonly property real bodyFontPx: 29
    readonly property real passageFontPx: 32

    // Count-up timer
    readonly property real countupY: 350
    readonly property real countupHeight: 175
    readonly property real countupFontPx: 150
    readonly property real minimumFittedFontPx: 12
    readonly property string timerFontFamily: "Menlo"

    // Response timer
    readonly property real responseTimerSize: 175
    readonly property real responseTimerY: 350
    readonly property real responseTimerStrokeWidth: 9
    readonly property real responseTimerFontPx: 44

    // Captions: a reserved band below slide content and timers.
    readonly property real captionBandHeight: 128

    // Captions
    readonly property color captionText: "white"
    readonly property color captionBackground: "#050a0e"
    readonly property real captionFontPx: 31
    readonly property real captionBottomMargin: 24
    readonly property real captionSideMargin: 50
    readonly property real captionPaddingX: 18
    readonly property real captionPaddingY: 12
    readonly property real captionRadius: 8
}
