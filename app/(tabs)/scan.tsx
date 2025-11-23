import { useThemeColor } from "@/hooks/use-theme-color";
import { CameraView, useCameraPermissions } from "expo-camera";
import { StatusBar } from "expo-status-bar";
import { useRef, useState } from "react";
import {
  Button,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function ScanScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [photo, setPhoto] = useState<string | null>(null);
  const cameraRef = useRef<CameraView>(null);
  const backgroundColor = useThemeColor({}, "background");
  const buttonColor = useThemeColor(
    { light: "#f0f0f0", dark: "#333" },
    "background"
  );
  const textColor = useThemeColor({}, "text");

  if (!permission) {
    // Camera permissions are still loading.
    return <View />;
  }

  if (!permission.granted) {
    // Camera permissions are not granted yet.
    return (
      <View style={[styles.container, { backgroundColor }]}>
        <Text style={[styles.message, { color: textColor }]}>
          We need your permission to show the camera
        </Text>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  const takePicture = async () => {
    if (cameraRef.current) {
      const photo = await cameraRef.current.takePictureAsync();
      setPhoto(photo?.uri || null);
    }
  };

  const retakePicture = () => {
    setPhoto(null);
  };

  const submitReceipt = () => {
    // TODO: Implement receipt processing logic here
    alert("Receipt submitted! (Mock)");
    setPhoto(null);
  };

  if (photo) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor }]}>
        <StatusBar style="auto" />
        <View style={[styles.previewContainer, { backgroundColor }]}>
          <Image source={{ uri: photo }} style={styles.previewImage} />
          <View style={[styles.buttonContainer, { backgroundColor }]}>
            <TouchableOpacity
              style={[styles.button, { backgroundColor: buttonColor }]}
              onPress={retakePicture}
            >
              <Text style={[styles.text, { color: textColor }]}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.submitButton]}
              onPress={submitReceipt}
            >
              <Text style={[styles.text, { color: "#fff" }]}>Submit</Text>
            </TouchableOpacity>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <CameraView style={styles.camera} facing="back" ref={cameraRef}>
        <View style={styles.cameraControls}>
          <TouchableOpacity style={styles.captureButton} onPress={takePicture}>
            <View style={styles.captureButtonInner} />
          </TouchableOpacity>
        </View>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
  },
  message: {
    textAlign: "center",
    paddingBottom: 10,
  },
  camera: {
    flex: 1,
  },
  cameraControls: {
    flex: 1,
    backgroundColor: "transparent",
    flexDirection: "row",
    justifyContent: "center",
    margin: 64,
  },
  captureButton: {
    alignSelf: "flex-end",
    alignItems: "center",
    justifyContent: "center",
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: "rgba(255, 255, 255, 0.3)",
    borderWidth: 4,
    borderColor: "white",
  },
  captureButtonInner: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: "white",
  },
  previewContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  previewImage: {
    flex: 1,
    width: "100%",
    resizeMode: "contain",
  },
  buttonContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
    width: "100%",
    padding: 20,
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 30,
    borderRadius: 8,
  },
  submitButton: {
    backgroundColor: "#000",
  },
  text: {
    fontSize: 16,
    fontWeight: "bold",
  },
});
