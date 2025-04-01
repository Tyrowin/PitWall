# telemetry/views.py
from django.shortcuts import render, redirect
from django.urls import reverse
import fastf1 as ff1
import logging
import pandas as pd # Import pandas

# Configure logging (optional, but helpful for debugging FastF1 issues)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def select_session(request):
    # ... (keep the existing select_session view as is) ...
    if request.method == 'POST':
        year = request.POST.get('year')
        gp = request.POST.get('gp')
        session_type = request.POST.get('session_type')

        # Basic validation (more robust validation needed for production)
        if year and gp and session_type:
            try:
                year = int(year)
                # Redirect to the display view with parameters in the URL
                return redirect(
                    reverse(
                        'display_data',
                        kwargs={
                            'year': year,
                            'gp': gp,
                            'session_type': session_type,
                        },
                    )
                )
            except ValueError:
                # Handle case where year is not an integer
                context = {'error': 'Year must be a number.'}
                return render(
                    request, 'telemetry/select_session.html', context
                )
        else:
            # Handle missing fields
            context = {'error': 'All fields are required.'}
            return render(request, 'telemetry/select_session.html', context)

    # If GET request, just display the form
    return render(request, 'telemetry/select_session.html')


def display_session_data(request, year, gp, session_type):
    """
    Fetches session data using FastF1 based on URL parameters
    and displays the race results.
    """
    context = {
        'year': year,
        'gp': gp,
        'session_type': session_type,
        'session_info': None,
        'race_results': None, # Changed from 'drivers'
        'error': None,
    }
    try:
        logger.info(
            f"Attempting to load session: Year={year}, GP={gp}, Type={session_type}"
        )
        # Load the session
        # Using event names might be more robust if GP names vary slightly
        # event = ff1.get_event(year, gp)
        # session = ff1.get_session(event.year, event.EventName, session_type)
        # For simplicity now, we stick to the direct approach:
        session = ff1.get_session(year, gp, session_type)

        # Load data - laps=True is needed to get results correctly populated
        # You might add weather=True or messages=True later if needed
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        logger.info(f"Session '{session.name}' loaded successfully.")

        context['session_info'] = {
            'name': session.name,
            'date': session.date.strftime('%Y-%m-%d %H:%M'),
            'event_name': session.event['EventName'],
            'location': session.event['Location'],
        }

        # --- Get Race Results ---
        # session.results is a Pandas DataFrame
        results_df = session.results

        if results_df is not None and not results_df.empty:
            # Select and rename columns for clarity in the template
            # Adjust columns based on what's available and needed
            results_df = results_df[[
                'Position',
                'Abbreviation',
                'TeamName',
                'GridPosition',
                'Status',
                'Points',
                'Time', # This is often a Timedelta object
                # 'Q1', 'Q2', 'Q3' # Available for qualifying
                # 'FastestLap' # Often needs joining with lap data
            ]].copy() # Use .copy() to avoid SettingWithCopyWarning

            # Convert Timedelta 'Time' to string for easier template display
            # Handle NaT (Not a Time) for drivers who didn't finish with a time
            if 'Time' in results_df.columns:
                 results_df['TimeString'] = results_df['Time'].apply(
                     lambda x: str(x.total_seconds()) + 's' if pd.notna(x) else ''
                 )
                 # Or format more nicely later: e.g., +1 Lap, +30.123s

            # Convert DataFrame to a list of dictionaries for the template
            context['race_results'] = results_df.to_dict('records')
        else:
             logger.warning("No results data found for this session.")
             context['race_results'] = [] # Ensure it's an empty list if no data


    except ff1.ErgastConnectionError as e:
         logger.error(f"Ergast connection error: {e}")
         context['error'] = f"Could not connect to Ergast API. Please check your internet connection and try again. Details: {e}"
    except ff1.cache.CacheEnabledLockedError as e:
         logger.error(f"FastF1 Cache Locked: {e}")
         context['error'] = f"FastF1 cache is locked. Another process might be using it. Please wait or clear the lock manually. Details: {e}"
    except ff1.errors.SessionNotAvailableError as e:
        logger.error(f"Session not available: {e}")
        context['error'] = f"The requested session ({year} {gp} {session_type}) is not available or does not have data. Please check the inputs. Error: {e}"
    except Exception as e:
        # Catch other potential errors
        logger.error(f"Error loading session data: {e}", exc_info=True)
        context['error'] = f"Could not load session data for {year} {gp} {session_type}. Please check the inputs or try later. Error: {e}"

    return render(request, 'telemetry/display_data.html', context)

