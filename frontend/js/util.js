function formatted_time(time) {
    return ((time.getHours() < 10)?"0":"") + time.getHours()
        + ":" + ((time.getMinutes() < 10)?"0":"") + time.getMinutes()
        + ":" + ((time.getSeconds() < 10)?"0":"") + time.getSeconds();
}

function now_ISOstring() {
    const timezone_offset = (new Date()).getTimezoneOffset() * 60000;
    return (new Date(Date.now() - timezone_offset)).toISOString().slice(0, -1);
}

async function fetch_with_timeout(resource, options={}) {
    const { timeout = 100000 } = options;

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(resource, {
        ...options,
        signal: controller.signal
    });
    clearTimeout(id);

    return response;
}

async function request(url, method, body, error_callback, success_callback) {
    let response;
    try {
        if (method == 'GET') {
            response = await fetch_with_timeout(url);
        } else {
            response = await fetch_with_timeout(url, {
                method: method,
                headers: {'Content-Type': 'text/plain'},
                body: JSON.stringify(body)
            });
        }
    } catch (error) {
        console.log(error);
        error_callback();
        return null;
    }

    if (response.status < 200 || response.status > 299) {
        console.log(response.status, response.statusText);
        const data = await response.json();
        console.log(data);
        error_callback();
        return null;
    }

    success_callback();
    const data = await response.json();
    return data;
}

async function button_request(
    url, method, body, button_key, confirm_prompt, ask, button_status, error_callback
) {
    if (ask) {
        if (!confirm(confirm_prompt)) return null;
    }

    button_status[button_key] = 'status-pending';

    return request(
        url, method, body,
        () => {
            button_status[button_key] = 'status-failure';
            error_callback();
        },
        () => {
            button_status[button_key] = 'status-success';
        }
    );

    // let response;
    // try {
    //     if (method == 'GET') {
    //         response = await fetch_with_timeout(url);
    //     } else {
    //         response = await fetch_with_timeout(url, {
    //             method: method,
    //             headers: {'Content-Type': 'application/json'},
    //             body: JSON.stringify(body)
    //         });
    //     }
    // } catch (error) {
    //     button_status[button_key] = 'status-failure';
    //     console.log(error);
    //     error_callback();
    //     return null;
    // }

    // if (response.status < 200 || response.status > 299) {
    //     button_status[button_key] = 'status-failure';
    //     console.log(response.status, response.statusText);
    //     const data = await response.json();
    //     console.log(data);
    //     error_callback();
    //     return null;
    // }

    // button_status[button_key] = 'status-success';
    // const data = await response.json();
    // return data;
}