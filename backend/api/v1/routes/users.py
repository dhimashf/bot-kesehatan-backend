from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from backend.services import web_auth_service, user_service
from backend.api.v1.schemas.user import User, UserProfile, FullUserProfileResponse, HealthResultPayload, HealthResultSummary, HealthResultBase
from core.services.profiling_service import profiling_service

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(web_auth_service.get_current_active_user)):
    """
    Get current logged-in user's basic information.
    """
    return current_user

@router.get("/profile/status")
def get_user_profile_status(
    current_user: dict = Depends(web_auth_service.get_current_active_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Check if the user has completed their identity profile and has at least one health result.
    """
    user_id = current_user.get("id")
    status = user_service.check_user_profile_status(db, user_id)
    return status

@router.get("/profile/full", response_model=FullUserProfileResponse)
def get_user_full_profile(
    current_user: dict = Depends(web_auth_service.get_current_active_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Get the user's full profile, including biodata and latest health results.
    """
    user_id = current_user.get("id")
    full_profile_data = web_auth_service.get_user_full_profile_by_id(db, user_id)

    # Ensure biodata is properly converted to dict (in case it's a DictRow)
    if full_profile_data.get("biodata"):
        biodata = full_profile_data["biodata"]
        if not isinstance(biodata, dict):
            biodata = dict(biodata)
        full_profile_data["biodata"] = biodata

    # Proses hasil kesehatan untuk menambahkan interpretasi/kategori
    if full_profile_data.get("health_results"):
        processed_results = []
        for hr in full_profile_data["health_results"]:
            # Ensure hr is a dict (convert if it's DictRow)
            if not isinstance(hr, dict):
                hr = dict(hr)
            
            # Mengambil nilai dengan .get() untuk menghindari KeyError jika kunci tidak ada
            # Memberikan nilai default 0 jika tidak ada, agar tidak terjadi TypeError
            who5_total = hr.get('who5_total', 0)
            gad7_total = hr.get('gad7_total', 0)
            k10_total = hr.get('k10_total', 0)
            mbi_emosional_total = hr.get('mbi_emosional_total', 0)
            mbi_sinis_total = hr.get('mbi_sinis_total', 0)
            mbi_pencapaian_total = hr.get('mbi_pencapaian_total', 0)
            naqr_pribadi_total = hr.get('naqr_pribadi_total', 0)
            naqr_pekerjaan_total = hr.get('naqr_pekerjaan_total', 0)
            naqr_intimidasi_total = hr.get('naqr_intimidasi_total', 0)
            naqr_bullying_experience = hr.get('naqr_bullying_experience') # Bisa None
            naqr_bullying_actors = hr.get('naqr_bullying_actors') # Bisa None
            naqr_bullying_perpetrators_detail = hr.get('naqr_bullying_perpetrators_detail') # Bisa None

            who5_cat = profiling_service.get_who5_category_from_total(who5_total)
            gad7_cat = profiling_service.get_gad7_category_from_total(gad7_total)
            k10_cat = profiling_service.get_k10_category_from_total(k10_total)
            mbi_ee_cat = profiling_service.get_mbi_category('emosional', mbi_emosional_total)
            mbi_cyn_cat = profiling_service.get_mbi_category('sinis', mbi_sinis_total)
            mbi_pa_cat = profiling_service.get_mbi_category('pencapaian', mbi_pencapaian_total)

            naqr_total = naqr_pribadi_total + naqr_pekerjaan_total + naqr_intimidasi_total
            naqr_cat = profiling_service.get_naqr_category_from_total(naqr_total)

            processed_hr = hr.copy()
            processed_hr.update({
                "who5_category": who5_cat,
                "gad7_category": gad7_cat,
                "k10_category": k10_cat,
                "mbi_emosional_category": mbi_ee_cat,
                "mbi_sinis_category": mbi_cyn_cat,
                "mbi_pencapaian_category": mbi_pa_cat,
                "mbi_total": mbi_emosional_total + mbi_sinis_total + mbi_pencapaian_total,
                "naqr_total": naqr_total,
                "naqr_category": naqr_cat,
                "naqr_bullying_experience": naqr_bullying_experience,
                "naqr_bullying_actors": naqr_bullying_actors,
                "naqr_bullying_perpetrators_detail": naqr_bullying_perpetrators_detail
            })
            processed_results.append(processed_hr)
        full_profile_data["health_results"] = processed_results

    # Determine completion status for frontend convenience
    biodata_completed = full_profile_data.get("biodata") is not None
    health_results_completed = bool(full_profile_data.get("health_results")) # bool() is fine for lists

    return FullUserProfileResponse(
        biodata=full_profile_data.get("biodata"),
        health_results=full_profile_data.get("health_results"),
        biodata_completed=biodata_completed,
        health_results_completed=health_results_completed
    )

@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_or_update_user_profile(
    profile_data: UserProfile,
    current_user: dict = Depends(web_auth_service.get_current_active_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Create or update the user's identity profile (biodata).
    Applies validation including gender-specific rules for status_kehamilan.
    """
    user_id = current_user.get("id")
    
    # Convert Pydantic model to dict for validation and processing
    biodata_dict = profile_data.model_dump(by_alias=True)
    
    # Apply validation from profiling_service (gender-specific validation for status_kehamilan)
    try:
        profiling_service.validate_biodata(biodata_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # The service handles the logic of insert vs update
    profiling_service.save_user_profile(user_id, biodata_dict)
    return {"message": "Profile saved successfully"}


@router.get("/questionnaire/{q_type}")
def get_questionnaire_data(q_type: str, current_user: dict = Depends(web_auth_service.get_current_active_user)):
    """
    Get questions and options for a specific questionnaire type.
    """
    questions = []
    options = []

    if q_type == 'who5':
        questions = profiling_service.who5_questions
        questions = [{"text": q} for q in profiling_service.who5_questions]
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.who5_options] # Tetap kirim skor ke FE
    elif q_type == 'gad7':
        questions = profiling_service.gad7_questions
        questions = [{"text": q} for q in profiling_service.gad7_questions]
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.gad7_options] # Tetap kirim skor ke FE
    elif q_type == 'mbi':
        questions = profiling_service.mbi_questions
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.mbi_options] # Tetap kirim skor ke FE
    elif q_type == 'naqr':
        # Endpoint ini sekarang hanya mengembalikan pertanyaan NAQR utama (58-79)
        questions = profiling_service.naqr_questions
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.naqr_options]
    elif q_type == 'k10':
        questions = profiling_service.k10_questions
        questions = [{"text": q} for q in profiling_service.k10_questions]
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.k10_options] # Tetap kirim skor ke FE
    elif q_type == 'naqr_perundungan':
        # Endpoint baru untuk kuesioner perundungan
        # Mengembalikan struktur yang lebih detail untuk ditangani frontend
        q_data = [
            {
                "id": "q80", "type": "multiple_choice", "text": profiling_service.naqr_perundungan_questions[0],
                "options": [{"text": opt[0], "score": opt[1]} for opt in profiling_service.NAQR_BULLYING_EXPERIENCE_OPTIONS]
            },
            {"id": "q81", "type": "text_input", "text": profiling_service.naqr_perundungan_questions[1]},
            {"id": "q82", "type": "text_input", "text": profiling_service.naqr_perundungan_questions[2]}
        ]
        return {"type": q_type, "questions": q_data}
    else:
        raise HTTPException(status_code=404, detail="Questionnaire type not found")

    return {"type": q_type, "questions": questions, "options": options}


@router.post("/profile/results", response_model=HealthResultSummary)
def submit_health_results(
    payload: HealthResultPayload,
    current_user: dict = Depends(web_auth_service.get_current_active_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Receive questionnaire scores, process them, save to DB, and return a summary.
    SECURITY: Ensures that the user has completed their biodata first.
    """
    user_id = current_user.get("id")

    # --- SECURITY CHECK ---
    # Verifikasi bahwa pengguna telah melengkapi biodata sebelum mengirimkan hasil.
    # Ini menutup celah di mana pengguna yang sudah login dapat langsung "menembak" API ini.
    profile_status = user_service.check_user_profile_status(db, user_id)
    if not profile_status.get('biodata_completed'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda harus melengkapi biodata terlebih dahulu sebelum mengirimkan hasil kuesioner."
        )

    # Process MBI scores
    mbi_result = profiling_service.get_mbi_result(payload.mbi_scores)
    # PERUBAHAN: Proses skor mentah NAQ-R di backend
    naqr_result = profiling_service.get_naqr_result(payload.naqr_scores)

    # Prepare data for DB insertion
    health_data_to_save = {
        'user_id': user_id,
        'who5_total': payload.who5_total,
        'gad7_total': payload.gad7_total,
        'k10_total': payload.k10_total,
        'mbi_emosional_total': mbi_result['emosional'][0],
        'mbi_sinis_total': mbi_result['sinis'][0],
        'mbi_pencapaian_total': mbi_result['pencapaian'][0],
        'naqr_pribadi_total': naqr_result['pribadi'],
        'naqr_pekerjaan_total': naqr_result['pekerjaan'],
        'naqr_intimidasi_total': naqr_result['intimidasi'],
        # Tambahkan field kuesioner perundungan dari payload
        'naqr_bullying_experience': payload.naqr_bullying_experience,
        'naqr_bullying_actors': payload.naqr_bullying_actors,
        'naqr_bullying_perpetrators_detail': payload.naqr_bullying_perpetrators_detail,
    }

    try:
        profiling_service.save_health_results(health_data_to_save)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save results: {e}")

    # Prepare summary for the frontend
    who5_interp = profiling_service.get_who5_category_from_total(payload.who5_total)
    gad7_interp = profiling_service.get_gad7_category_from_total(payload.gad7_total)
    k10_interp = profiling_service.get_k10_category_from_total(payload.k10_total)

    naqr_interp = naqr_result['category']

    summary = {
        "WHO-5": {"score": payload.who5_total, "interpretation": who5_interp},
        "GAD-7": {"score": payload.gad7_total, "interpretation": gad7_interp},
        "MBI-EE": {"score": mbi_result['emosional'][0], "interpretation": mbi_result['emosional'][1]},
        "MBI-CYN": {"score": mbi_result['sinis'][0], "interpretation": mbi_result['sinis'][1]},
        "MBI-PA": {"score": mbi_result['pencapaian'][0], "interpretation": mbi_result['pencapaian'][1]},
        "NAQ-R Total": {"score": naqr_result['total'], "interpretation": naqr_interp},
        "K-10": {"score": payload.k10_total, "interpretation": k10_interp},
    }
    
    # Tambahkan detail perundungan ke ringkasan jika ada
    if payload.naqr_bullying_experience is not None and payload.naqr_bullying_experience > 1:
        experience_label = next((label for label, val in profiling_service.NAQR_BULLYING_EXPERIENCE_OPTIONS if val == payload.naqr_bullying_experience), "Tidak Diketahui")
        bullying_summary = {
            "Pengalaman": experience_label,
        }
        if payload.naqr_bullying_actors:
            bullying_summary["Pelaku"] = payload.naqr_bullying_actors
        if payload.naqr_bullying_perpetrators_detail:
            bullying_summary["Detail Pelaku"] = payload.naqr_bullying_perpetrators_detail
        
        # Tambahkan objek ringkasan perundungan sebagai item baru di summary
        summary["Detail Pengalaman Perundungan"] = bullying_summary

    return {"message": "Results saved successfully", "summary": summary}

@router.delete("/profile/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_health_result(
    result_id: int,
    current_user: dict = Depends(web_auth_service.get_current_active_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Delete a specific health result entry by its ID.
    Ensures that a user can only delete their own results.
    """
    user_id = current_user.get("id")
    success = db.delete_health_result_by_id(result_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Result not found or you do not have permission to delete it.")
    return

@router.delete("/admin/health-results/{result_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin"])
def delete_health_result_admin(
    result_id: int,
    admin_user: dict = Depends(web_auth_service.get_current_admin_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    (Admin only) Menghapus entri health result tertentu berdasarkan ID-nya.
    Ini tidak memeriksa user_id, memungkinkan admin menghapus riwayat apapun.
    """
    success = db.delete_health_result_by_id_admin(result_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Health result with ID {result_id} not found.")
    return


# --- Admin Routes ---

@router.get("/admin/all-users", response_model=List[User], tags=["Admin"])
def get_all_users(
    admin_user: dict = Depends(web_auth_service.get_current_admin_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """Get all users. Requires admin privileges."""
    users_data = db.get_all_users()
    # Konversi setiap baris (yang mungkin berupa DictRow) menjadi dictionary standar
    return [dict(user) for user in users_data]

@router.get("/admin/all-profiles", tags=["Admin"])
def get_all_profiles(
    admin_user: dict = Depends(web_auth_service.get_current_admin_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """Get all user profiles. Requires admin privileges."""
    return db.get_all_profiles()

@router.get("/admin/all-health-results", tags=["Admin"])
def get_all_health_results(
    admin_user: dict = Depends(web_auth_service.get_current_admin_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """Get all health results from all users. Requires admin privileges."""
    return db.get_all_health_results_admin()

@router.get("/admin/all-results-with-biodata", tags=["Admin"])
def get_all_results_with_biodata(
    admin_user: dict = Depends(web_auth_service.get_current_admin_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Get all users with their profile completion status, biodata, and health results.
    Requires admin privileges.
    """
    # PENDEKATAN OPTIMAL: Gunakan satu query JOIN untuk mengambil semua data
    all_data = db.get_all_users_with_status_and_data_admin()
    
    users_dict = {}
    biodata_keys = [
        'inisial', 'no_wa', 'usia', 'jenis_kelamin', 'pendidikan', 'lama_bekerja', 
        'status_pegawai', 'jabatan', 'jabatan_lain', 'unit_ruangan', 
        'status_perkawinan', 'status_kehamilan', 'jumlah_anak'
    ]
    health_result_keys = [
        'health_result_id', 'who5_total', 'gad7_total', 'mbi_emosional_total', 
        'mbi_sinis_total', 'mbi_pencapaian_total', 'naqr_pribadi_total', 
        'naqr_pekerjaan_total', 'naqr_intimidasi_total', 'k10_total', 'created_at',
        'naqr_bullying_experience', 'naqr_bullying_actors',
        'naqr_bullying_perpetrators_detail'
    ]

    for row in all_data:
        user_id = row['user_id']
        if user_id not in users_dict:
            # Buat entri pengguna baru jika belum ada
            biodata = {key: row[key] for key in biodata_keys if row[key] is not None}
            biodata['user_id'] = user_id
            biodata['email'] = row['email']
            biodata['role'] = row['role']

            # Cek kelengkapan biodata
            required_fields = [f for f in biodata_keys if f != 'jabatan_lain']
            biodata_completed = all(row.get(field) is not None for field in required_fields)

            users_dict[user_id] = {
                "biodata_completed": biodata_completed,
                "health_results_completed": False, # Default, akan di-update jika ada hasil
                "biodata": biodata,
                "health_results": []
            }

        # Tambahkan hasil kuesioner jika ada
        if row['health_result_id'] is not None:
            users_dict[user_id]['health_results_completed'] = True
            health_result = {key: row[key] for key in health_result_keys}
            # Ganti nama 'health_result_id' menjadi 'id' agar konsisten dengan skema
            health_result['id'] = health_result.pop('health_result_id')
            users_dict[user_id]['health_results'].append(health_result)

    return list(users_dict.values())


@router.get("/admin/profile/{user_id}", response_model=FullUserProfileResponse, tags=["Admin"])
def get_user_profile_by_id_admin(
    user_id: int,
    admin_user: dict = Depends(web_auth_service.get_current_admin_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Get a specific user's full profile by their ID. Requires admin privileges.
    """
    full_profile_data = web_auth_service.get_user_full_profile_by_id(db, user_id)

    # Jika tidak ada data sama sekali (bahkan akun user tidak ada)
    if not full_profile_data:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")

    # Ensure biodata is properly converted to dict (in case it's a DictRow)
    if full_profile_data.get("biodata"):
        biodata = full_profile_data["biodata"]
        if not isinstance(biodata, dict):
            biodata = dict(biodata)
        full_profile_data["biodata"] = biodata

    # Proses hasil kesehatan untuk menambahkan interpretasi/kategori (logika yang sama dengan /profile/full)
    if full_profile_data.get("health_results"):
        processed_results = []
        for hr in full_profile_data["health_results"]:
            # Ensure hr is a dict (convert if it's DictRow)
            if not isinstance(hr, dict):
                hr = dict(hr)
            
            who5_total = hr.get('who5_total', 0)
            gad7_total = hr.get('gad7_total', 0)
            k10_total = hr.get('k10_total', 0)
            mbi_emosional_total = hr.get('mbi_emosional_total', 0)
            mbi_sinis_total = hr.get('mbi_sinis_total', 0)
            mbi_pencapaian_total = hr.get('mbi_pencapaian_total', 0)
            naqr_pribadi_total = hr.get('naqr_pribadi_total', 0)
            naqr_pekerjaan_total = hr.get('naqr_pekerjaan_total', 0)
            naqr_intimidasi_total = hr.get('naqr_intimidasi_total', 0)
            naqr_bullying_experience = hr.get('naqr_bullying_experience')
            naqr_bullying_actors = hr.get('naqr_bullying_actors')
            naqr_bullying_perpetrators_detail = hr.get('naqr_bullying_perpetrators_detail')

            naqr_total = naqr_pribadi_total + naqr_pekerjaan_total + naqr_intimidasi_total

            processed_hr = hr.copy()
            processed_hr.update({
                "who5_category": profiling_service.get_who5_category_from_total(who5_total),
                "gad7_category": profiling_service.get_gad7_category_from_total(gad7_total),
                "k10_category": profiling_service.get_k10_category_from_total(k10_total),
                "mbi_emosional_category": profiling_service.get_mbi_category('emosional', mbi_emosional_total),
                "mbi_sinis_category": profiling_service.get_mbi_category('sinis', mbi_sinis_total),
                "mbi_pencapaian_category": profiling_service.get_mbi_category('pencapaian', mbi_pencapaian_total),
                "mbi_total": mbi_emosional_total + mbi_sinis_total + mbi_pencapaian_total,
                "naqr_total": naqr_total,
                "naqr_category": profiling_service.get_naqr_category_from_total(naqr_total),
                "naqr_bullying_experience": naqr_bullying_experience,
                "naqr_bullying_actors": naqr_bullying_actors,
                "naqr_bullying_perpetrators_detail": naqr_bullying_perpetrators_detail
            })
            processed_results.append(processed_hr)
        full_profile_data["health_results"] = processed_results

    # Tentukan status penyelesaian untuk kenyamanan frontend
    biodata_completed = full_profile_data.get("biodata") is not None
    health_results_completed = bool(full_profile_data.get("health_results"))

    return FullUserProfileResponse(
        biodata=full_profile_data.get("biodata"),
        health_results=full_profile_data.get("health_results"),
        biodata_completed=biodata_completed,
        health_results_completed=health_results_completed
    )

@router.get("/admin/health-results/{user_id}", response_model=List[HealthResultBase], tags=["Admin"])
def get_health_results_by_user_id_admin(
    user_id: int,
    admin_user: dict = Depends(web_auth_service.get_current_admin_user),
    db: web_auth_service.Database = Depends(web_auth_service.get_db)
):
    """
    Get all health results for a specific user by their ID. Requires admin privileges.
    """
    # Verifikasi apakah pengguna ada untuk memberikan pesan error yang jelas
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")

    # Gunakan kembali metode yang sudah ada untuk mengambil semua hasil
    results = db.get_all_health_results(user_id)
    # SOLUSI: Konversi setiap baris (yang mungkin berupa DictRow/tuple) menjadi dictionary standar
    # Ini memastikan data cocok dengan response_model=List[HealthResultBase]
    return [dict(result) for result in results]