// Read-only known blockers, NOT a vulnerability scanner or independent audit.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
function read(root,name){return fs.readFileSync(root+'/'+name,'utf8')}
export function inspect(root='.'){
 const db=read(root,'frontend/lib/data/drift/database.dart');
 const backup=read(root,'frontend/lib/data/drift/local_backup.dart');
 const main=read(root,'frontend/lib/main.dart');
 const controller=read(root,'frontend/lib/services/patient_vault_session_controller.dart');
 const gates={
  patientOpensPlainSqlite:db.includes("sqlite3Wasm: Uri.parse('sqlite3.wasm')")&&
    db.includes("AppDatabase.forPatientVault("),
  patientBackupReturnsPlainJson:backup.includes('static Future<String> exportVaultJson')&&
    backup.includes('return jsonEncode(envelope);'),
  productionControllerUsesUnkeyedFactory:controller.includes(
    '_openDatabase = openDatabase ?? AppDatabase.forPatientVault'),
  mainDoesNotGateDbAdmissionOnUnlock:main.includes(
    'PatientVaultSessionController.forAuth(authService)')&&
    !main.includes('D1VerifiedEncryptedVaultAdmission'),
  physicalSafariNotProvided:true,
  independentReviewerNotAssigned:true,
 };
 return {sha:process.env.GITHUB_SHA||'LOCAL_UNVERIFIED',lot:'D1_SECURITY_REVIEW',
  type:'INTERNAL_READ_ONLY_GATE',patientRelease:'NO_GO',
  blockers:gates,blockingCount:Object.values(gates).filter(Boolean).length,
  warning:'This detects known blockers only. CI GREEN does NOT certify the patient application.'};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const report=inspect();
 fs.writeFileSync('d1-security-no-go.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
}
