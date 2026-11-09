import Flutter
import UIKit

class SceneDelegate: FlutterSceneDelegate {
  // Scene-enabled iOS apps do not receive AppDelegate's corresponding
  // background/foreground events. Reapply the patient-only backup flag here.
  override func sceneDidEnterBackground(_ scene: UIScene) {
    super.sceneDidEnterBackground(scene)
    ClinicalVaultBackupExclusion.applyToDocumentsDirectory()
  }

  override func sceneWillEnterForeground(_ scene: UIScene) {
    super.sceneWillEnterForeground(scene)
    ClinicalVaultBackupExclusion.applyToDocumentsDirectory()
  }
}
