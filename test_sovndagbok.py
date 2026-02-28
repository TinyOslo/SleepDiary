import pytest  # type: ignore
from datetime import time, date, datetime, timedelta
from Sovndagbok import format_hours_as_hm, process_log_data  # type: ignore

# --- Tester for hjelpefunksjoner ---

def test_format_hours_as_hm():
    """Sjekker at tidsformatering fungerer for ulike verdier."""
    assert format_hours_as_hm(7.5) == "7 t 30 min"
    assert format_hours_as_hm(6.0) == "6 t"
    assert format_hours_as_hm(0.25) == "0 t 15 min"
    assert format_hours_as_hm(8.333) == "8 t 20 min"  # Rundes til nærmeste minutt

# --- Tester for databehandling og midnatt-logikk ---

def test_process_log_data_basic():
    """Tester en standard natt uten komplikasjoner."""
    test_data = {
        "2026-02-01": {
            "bed_time": "23:00:00",
            "lights_out": "23:15:00",
            "sleep_onset": "23:30:00",
            "wake_up": "07:00:00",
            "out_of_bed": "07:15:00",
            "waso_minutes": 15,
            "nap_minutes": 0,
            "awakenings": []
        }
    }
    
    df = process_log_data(test_data)
    
    assert len(df) == 1
    row = df.iloc[0]
    
    # TIB (Time In Bed): 23:00 til 07:15 = 8t 15min = 495 min
    assert row["TIB_min"] == 495
    
    # TST (Total Sleep Time): (23:30 til 07:00) - 15 min WASO
    # 23:30 til 07:00 er 7t 30min = 450 min. 450 - 15 = 435 min.
    assert row["TST_min"] == 435
    
    # SE (Sleep Efficiency): (435 / 495) * 100 = 87.87...%
    assert pytest.approx(row["SE"], 0.1) == 87.9

def test_process_log_data_midnight_crossover():
    """Tester at logikken håndterer overgang ved midnatt korrekt (18:00 pivot)."""
    test_data = {
        "2026-02-01": {
            "bed_time": "22:00:00",      # Kveld
            "lights_out": "22:15:00",    # Kveld
            "sleep_onset": "22:30:00",   # Kveld
            "wake_up": "06:00:00",      # Morgen (neste dag)
            "out_of_bed": "06:15:00",    # Morgen (neste dag)
            "waso_minutes": 0,
            "nap_minutes": 0
        }
    }
    
    df = process_log_data(test_data)
    row = df.iloc[0]
    
    # Sjekk at datoene er riktig tolket (neste dag for morgen-tider)
    assert row["bed_dt"].date() == date(2026, 2, 1)
    assert row["out_dt"].date() == date(2026, 2, 2)
    
    # TIB: 22:00 til 06:15 = 8t 15min = 495 min
    assert row["TIB_min"] == 495

def test_process_log_data_empty():
    """Sjekker at funksjonen håndterer tomme data uten å krasje."""
    df = process_log_data({})
    assert df.empty

def test_process_log_data_waso_calculation():
    """Verifiserer at WASO blir trukket fra TST korrekt."""
    test_data = {
        "2026-02-01": {
            "bed_time": "23:00:00",
            "lights_out": "23:00:00",
            "sleep_onset": "23:00:00",
            "wake_up": "07:00:00",
            "out_of_bed": "07:00:00",
            "waso_minutes": 60, # 1 time våken i løpet av natten
            "nap_minutes": 0
        }
    }
    
    df = process_log_data(test_data)
    row = df.iloc[0]
    
    # TIB er 8 timer (480 min)
    # TST bør være 8 timer - 1 time = 7 timer (420 min)
    assert row["TST_min"] == 420
    assert row["SE"] == (420/480)*100
