import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasma5support as Plasma5Support

PlasmoidItem {
    id: root
    
    property var tasksList: []

    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        
        onNewData: (sourceName, data) => {
            var exitCode = data["exit code"]
            var stdout = data["stdout"]
            
            if (stdout) {
                try {
                    var parsed = JSON.parse(stdout)
                    // Only update if it's the list command
                    if (sourceName === "python3 /home/ramiro/Widget-Tareas-Pendientes/src/cli.py") {
                        root.tasksList = parsed
                    }
                } catch(e) {
                    console.log("Error parsing JSON:", e)
                }
            }
            disconnectSource(sourceName)
        }
    }

    function loadTasks() {
        var cmd = "python3 /home/ramiro/Widget-Tareas-Pendientes/src/cli.py"
        executable.connectSource(cmd)
    }

    function cycleTask(taskId) {
        var cmd = "python3 /home/ramiro/Widget-Tareas-Pendientes/src/cli.py --cycle " + taskId
        executable.connectSource(cmd)
        refreshTimer.restart()
    }
    
    function openApp() {
        var cmd = "systemd-run --user python3 /home/ramiro/Widget-Tareas-Pendientes/src/main.py"
        executable.connectSource(cmd)
    }

    Timer {
        id: refreshTimer
        interval: 500
        repeat: false
        onTriggered: root.loadTasks()
    }

    // Auto-refresh every 30 seconds to catch changes made from the main app
    Timer {
        id: autoRefresh
        interval: 30000
        repeat: true
        running: true
        onTriggered: root.loadTasks()
    }

    Component.onCompleted: {
        root.loadTasks()
    }

    fullRepresentation: Item {
        width: 340
        height: 420

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing

            // Header
            RowLayout {
                Layout.fillWidth: true
                
                Kirigami.Heading {
                    text: "Academic Tasks"
                    level: 2
                    Layout.fillWidth: true
                }
                
                Kirigami.Icon {
                    source: "view-refresh-symbolic"
                    isMask: true
                    width: Kirigami.Units.iconSizes.smallMedium
                    height: width
                    color: Kirigami.Theme.textColor
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.loadTasks()
                        cursorShape: Qt.PointingHandCursor
                        hoverEnabled: true
                    }
                }
                
                Kirigami.Icon {
                    source: "external-link-symbolic"
                    isMask: true
                    width: Kirigami.Units.iconSizes.smallMedium
                    height: width
                    color: Kirigami.Theme.textColor
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.openApp()
                        cursorShape: Qt.PointingHandCursor
                        hoverEnabled: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Kirigami.Theme.disabledTextColor
                opacity: 0.3
            }

            // Task List
            ListView {
                id: listView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: Kirigami.Units.smallSpacing
                model: root.tasksList

                delegate: Rectangle {
                    width: listView.width
                    height: col.implicitHeight + Kirigami.Units.largeSpacing * 2
                    color: Kirigami.Theme.backgroundColor
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                    radius: 6

                    RowLayout {
                        id: col
                        anchors.fill: parent
                        anchors.margins: Kirigami.Units.smallSpacing
                        spacing: Kirigami.Units.largeSpacing

                        // Status Button
                        Rectangle {
                            width: 24
                            height: 24
                            radius: 12
                            color: "transparent"
                            border.color: {
                                if (modelData.status === 0) return Kirigami.Theme.disabledTextColor;
                                if (modelData.status === 1) return Kirigami.Theme.textColor.hslLightness > 0.5 ? "#4da6ff" : "#0066cc"; // IN_PROGRESS
                                return Kirigami.Theme.positiveTextColor; // COMPLETED
                            }
                            border.width: 2
                            
                            Text {
                                anchors.centerIn: parent
                                text: modelData.icon
                                color: parent.border.color
                                font.pixelSize: 14
                                visible: modelData.status !== 0
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: root.cycleTask(modelData.id)
                                cursorShape: Qt.PointingHandCursor
                            }
                        }

                        // Text details
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            
                            Text {
                                text: modelData.title
                                color: modelData.status === 2 ? Kirigami.Theme.disabledTextColor : Kirigami.Theme.textColor
                                font.strikeout: modelData.status === 2
                                font.weight: Font.DemiBold
                                font.pixelSize: 13
                                Layout.fillWidth: true
                                wrapMode: Text.Wrap
                            }
                            
                            RowLayout {
                                spacing: Kirigami.Units.smallSpacing
                                
                                Rectangle {
                                    color: "#8b5cf6" // Solid vibrant violet
                                    opacity: 1.0
                                    radius: 4
                                    Layout.preferredHeight: subjText.implicitHeight + 6
                                    Layout.preferredWidth: subjText.implicitWidth + 12
                                    
                                    Text {
                                        id: subjText
                                        anchors.centerIn: parent
                                        text: modelData.subject
                                        color: "#ffffff" // Pure white text
                                        font.pixelSize: 11
                                        font.weight: Font.Bold
                                    }
                                }
                                
                                Text {
                                    text: modelData.due
                                    color: Kirigami.Theme.textColor.hslLightness > 0.5 ? "#ff6b6b" : "#d32f2f"
                                    font.pixelSize: 11
                                    visible: modelData.due !== ""
                                }
                            }
                        }
                    }
                }
                
                Text {
                    anchors.centerIn: parent
                    text: "No tasks found.\nClick external link to add one."
                    horizontalAlignment: Text.AlignHCenter
                    visible: root.tasksList.length === 0
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }
    }
}
