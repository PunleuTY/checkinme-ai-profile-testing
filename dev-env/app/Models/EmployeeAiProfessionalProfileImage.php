<?php

namespace App\Models;

use App\Http\Traits\MediaTrait;
use Illuminate\Database\Eloquent\Model;
use App\Http\Traits\CreateUpdateDeleteByTrait;
use Illuminate\Database\Eloquent\SoftDeletes;

/**
 * Table: employee_ai_professional_profile_images
 *
 * Columns:
 *   id                  bigint PK
 *   employee_id         FK → employees.id
 *   original_image_id   FK → media.id (nullable)  — the photo the employee uploaded
 *   data                longText JSON (nullable)   — JSON array of generated Media IDs
 *   masked_image_id     FK → media.id (nullable)  — reserved (added in 2nd migration)
 *   modified_image_id   FK → media.id (nullable)  — reserved (added in 2nd migration)
 *   deleted_at          softDelete timestamp
 *   created_at / updated_at
 *
 * Relationships on Employee model:
 *   $employee->aiProfiles      → hasMany (all records for this employee)
 *   $employee->latestAiProfile → hasOne  (latest record, used as current session)
 */
class EmployeeAiProfessionalProfileImage extends Model
{
    use CreateUpdateDeleteByTrait;
    use MediaTrait;
    use SoftDeletes;

    protected $guarded = ['created_at', 'updated_at'];
}
