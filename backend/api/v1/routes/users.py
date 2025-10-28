from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from backend.services import web_auth_service, user_service
from backend.api.v1.schemas.user import User, UserProfile, LatestHealthResult, FullUserProfileResponse, HealthResultPayload, HealthResultSummary
from core.services.profiling_service import profiling_service

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(web_auth_service.get_current_active_user)):
    """
    Get current logged-in user's basic information.
    """
    return current_user

@router.get("/profile/status")
def get_user_profile_status(current_user: dict = Depends(web_auth_service.get_current_active_user)):
    """
    Check if the user has completed their identity profile and has at least one health result.
    """
    user_id = current_user.get("id")
    status = user_service.check_user_profile_status(user_id)
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

    # Proses hasil kesehatan untuk menambahkan interpretasi/kategori
    if full_profile_data.get("health_results"):
        processed_results = []
        for hr in full_profile_data["health_results"]:
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

            who5_cat = profiling_service.get_who5_category_from_total(who5_total)
            gad7_cat = profiling_service.get_gad7_category_from_total(gad7_total)
            k10_cat = profiling_service.get_k10_category_from_total(k10_total)
            mbi_ee_cat = profiling_service.get_mbi_category('emosional', mbi_emosional_total)
            mbi_cyn_cat = profiling_service.get_mbi_category('sinis', mbi_sinis_total)
            mbi_pa_cat = profiling_service.get_mbi_category('pencapaian', mbi_pencapaian_total)

            processed_hr = hr.copy()
            processed_hr.update({
                "who5_category": who5_cat,
                "gad7_category": gad7_cat,
                "k10_category": k10_cat,
                "mbi_emosional_category": mbi_ee_cat,
                "mbi_sinis_category": mbi_cyn_cat,
                "mbi_pencapaian_category": mbi_pa_cat,
                "mbi_total": mbi_emosional_total + mbi_sinis_total + mbi_pencapaian_total,
                "naqr_total": naqr_pribadi_total + naqr_pekerjaan_total + naqr_intimidasi_total
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
    current_user: dict = Depends(web_auth_service.get_current_active_user)
):
    """
    Create or update the user's identity profile (biodata).
    """
    user_id = current_user.get("id")
    # The service handles the logic of insert vs update
    profiling_service.save_user_profile(user_id, profile_data.model_dump(by_alias=True))
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
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.who5_options]
    elif q_type == 'gad7':
        questions = profiling_service.gad7_questions
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.gad7_options]
    elif q_type == 'mbi':
        questions = profiling_service.mbi_questions
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.mbi_options]
    elif q_type == 'naqr':
        questions = profiling_service.naqr_questions
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.naqr_options]
    elif q_type == 'k10':
        questions = profiling_service.k10_questions
        options = [{"text": opt[0], "score": opt[1]} for opt in profiling_service.k10_options]
    else:
        raise HTTPException(status_code=404, detail="Questionnaire type not found")

    return {"type": q_type, "questions": questions, "options": options}


@router.post("/profile/results", response_model=HealthResultSummary)
def submit_health_results(
    payload: HealthResultPayload,
    current_user: dict = Depends(web_auth_service.get_current_active_user)
):
    """
    Receive questionnaire scores, process them, save to DB, and return a summary.
    """
    user_id = current_user.get("id")

    # Process MBI scores
    mbi_result = profiling_service.get_mbi_result(payload.mbi_scores)

    # Prepare data for DB insertion
    health_data_to_save = {
        'user_id': user_id,
        'who5_total': payload.who5_total,
        'gad7_total': payload.gad7_total,
        'mbi_emosional_total': mbi_result['emosional'][0],
        'mbi_sinis_total': mbi_result['sinis'][0],
        'mbi_pencapaian_total': mbi_result['pencapaian'][0],
        'naqr_pribadi_total': payload.naqr_pribadi_total,
        'naqr_pekerjaan_total': payload.naqr_pekerjaan_total,
        'naqr_intimidasi_total': payload.naqr_intimidasi_total,
        'k10_total': payload.k10_total
    }

    try:
        profiling_service.save_health_results(health_data_to_save)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save results: {e}")

    # Prepare summary for the frontend
    _, who5_interp = profiling_service.get_who5_result([payload.who5_total])
    _, gad7_interp = profiling_service.get_gad7_result([payload.gad7_total])
    _, k10_interp = profiling_service.get_k10_result([payload.k10_total])

    summary = {
        "WHO-5": {"score": payload.who5_total, "interpretation": who5_interp},
        "GAD-7": {"score": payload.gad7_total, "interpretation": gad7_interp},
        "MBI-EE": {"score": mbi_result['emosional'][0], "interpretation": mbi_result['emosional'][1]},
        "MBI-CYN": {"score": mbi_result['sinis'][0], "interpretation": mbi_result['sinis'][1]},
        "MBI-PA": {"score": mbi_result['pencapaian'][0], "interpretation": mbi_result['pencapaian'][1]},
        "NAQ-R Pribadi": {"score": payload.naqr_pribadi_total, "interpretation": "N/A"},
        "NAQ-R Pekerjaan": {"score": payload.naqr_pekerjaan_total, "interpretation": "N/A"},
        "NAQ-R Intimidasi": {"score": payload.naqr_intimidasi_total, "interpretation": "N/A"},
        "K-10": {"score": payload.k10_total, "interpretation": k10_interp},
    }

    return {"message": "Results saved successfully", "summary": summary}

@router.delete("/profile/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_health_result(
    result_id: int,
    current_user: dict = Depends(web_auth_service.get_current_active_user)
):
    """
    Delete a specific health result entry by its ID.
    Ensures that a user can only delete their own results.
    """
    user_id = current_user.get("id")
    from core.services.database import Database
    db = Database()
    success = db.delete_health_result_by_id(result_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Result not found or you do not have permission to delete it.")
    return