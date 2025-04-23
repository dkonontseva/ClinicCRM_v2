class PatientAPI {
    static async getPatientProfile(patientId) {
        const response = await fetch(
            `/api/v1/clinic/patients/patient?id=${patientId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch patient data')
        }
        return await response.json()
    }

    static async updatePatientBasicInfo(patientId, data) {
        const response = await fetch(
            `/api/v1/clinic/patients/update/${patientId}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    users: {
                        first_name: data.first_name,
                        last_name: data.last_name,
                        second_name: data.second_name,
                        login: data.email,
                        phone_number: data.phone_number,
                        gender: data.gender,
                    },
                    b_date: data.date_of_birth,
                }),
            }
        )

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update patient data')
        }
        return await response.json()
    }

    static async updatePatientAddress(patientId, data) {
        const response = await fetch(
            `/api/v1/clinic/patients/update/${patientId}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    addresses: {
                        country: data.country,
                        city: data.city,
                        street: data.street,
                        house_number: data.house,
                        flat_number: data.flat ? parseInt(data.flat) : null,
                    },
                }),
            }
        )

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update address')
        }
        return await response.json()
    }

    static async updatePassword(userId, oldPassword, newPassword) {
        const response = await fetch(`/api/v1/clinic/auth/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                old_password: oldPassword,
                new_password: newPassword,
            }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update password')
        }
        return await response.json()
    }

    static async getDashboardData(patientId) {
        const response = await fetch(
            `/api/v1/clinic/patients/dashboard?patient_id=${patientId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data')
        }
        return await response.json()
    }

    static async getFutureTalons(patientId) {
        const response = await fetch(
            `/api/v1/clinic/patients/get_future_talon?patient_id=${patientId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch future talons')
        }
        return await response.json()
    }

    static async searchMedicalCards(patientName) {
        const response = await fetch(`/api/v1/clinic/patients/search/medical_cards?patient_name=${encodeURIComponent(patientName)}`)
        if (!response.ok) {
            throw new Error('Failed to search medical cards')
        }
        return await response.json()
    }


    static async getMedicalCards(patientId) {
        const response = await fetch(
            `/api/v1/clinic/patients/myCards?patient_id=${patientId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch medical cards')
        }
        return await response.json()
    }

    static async getMedicalCardNote(noteId) {
        const response = await fetch(`/api/v1/clinic/medical_cards/${noteId}`)
        if (!response.ok) {
            throw new Error('Failed to fetch medical card note')
        }
        return await response.json()
    }

    static async getAvailableTalons(doctorId, date) {
        const response = await fetch(
            `/api/v1/clinic/talons/available?doctor_id=${doctorId}&date=${date}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch available talons')
        }
        return await response.json()
    }

    static async bookTalon(doctorId, patientId, date, time, serviceId) {
        const response = await fetch(
            `/api/v1/clinic/talons/add?patient_id=${patientId}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    doctor_id: doctorId,
                    date: date,
                    time: time,
                    service_id: parseInt(serviceId),
                    status: 'pending',
                }),
            }
        )

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to book appointment')
        }
        return await response.json()
    }


    static async getAllServices() {
        const response = await fetch(`/api/v1/clinic/talons/services`)
        if (!response.ok) {
            throw new Error('Failed to fetch services')
        }
        return await response.json()
    }

}

class DoctorAPI {
    static async getDoctorProfile(doctorId) {
        const response = await fetch(
            `/api/v1/clinic/doctors/get_data?doctor_id=${doctorId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch doctor data')
        }
        return await response.json()
    }

    static async updateDoctorInfo(doctorId, data) {
        const response = await fetch(
            `/api/v1/clinic/doctors/update?doctor_id=${doctorId}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            }
        )
        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update doctor data')
        }
        return await response.json()
    }

    static async getDashboardData(doctorId) {
        const response = await fetch(
            `/api/v1/clinic/doctors/dashboard?doctor_id=${doctorId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data')
        }
        return await response.json()
    }

    static async getPatientCards(doctorId) {
        const response = await fetch(
            `/api/v1/clinic/doctors/patientsCards?doctor_id=${doctorId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data')
        }
        return await response.json()
    }

    static async getLeaves(doctorId) {
        const response = await fetch(
            `/api/v1/clinic/doctor_leaves/get_leaves?doctor_id=${doctorId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch leaves')
        }
        return await response.json()
    }

    static async addLeave(doctorId, leaveData) {
        const response = await fetch(
            `/api/v1/clinic/doctor_leaves/addLeave?doctor_id=${doctorId}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(leaveData),
            }
        )
        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to add leave')
        }
        return await response.json()
    }

    static async updateLeave(leaveId, data) {
        const response = await fetch(
            `/api/v1/clinic/doctor_leaves/update/${leaveId}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    leave_type: data.leave_type,
                    from_date: data.from_date,
                    to_date: data.to_date,
                    reason: data.reason,
                }),
            }
        )

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update leave')
        }
        return await response.json()
    }

    static async getMedicalCards(doctorId) {
        const response = await fetch(
            `/api/v1/clinic/doctors/medical_cards?doctor_id=${doctorId}`
        )
        if (!response.ok) {
            throw new Error('Failed to fetch medical cards')
        }
        return await response.json()
    }

    static async addMedicalNote(data) {
        const response = await fetch(`/api/v1/clinic/medical_cards/add_note`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patient_id: data.patient_id,
                doctor_id: data.doctor_id,
                date: data.date,
                symptoms: data.symptoms,
                results: data.results,
                diagnosis: data.diagnosis,
            }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to add medical note')
        }
        return await response.json()
    }

    static async updateAppointmentStatus(appointmentId, status) {
        const response = await fetch(
            `/api/v1/clinic/talons/update_status/${appointmentId}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    status: status,
                }),
            }
        )

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to update appointment status')
        }
        return await response.json()
    }
}
