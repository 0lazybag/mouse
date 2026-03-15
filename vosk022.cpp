#include <windows.h>
#include <iostream>
#include <string>

// Глобальная информация о процессе
PROCESS_INFORMATION piVosk = { 0 };

// --- Звуковые сигналы ---
void SoundStart() { Beep(600, 100); Beep(900, 150); }
void SoundStop() { Beep(900, 100); Beep(500, 150); }
void SoundError() { Beep(300, 500); }

// --- Управление процессом ---
void StartVoskProcess() {
    if (piVosk.hProcess != NULL) return;
    STARTUPINFOW si = { sizeof(si) };
    si.cb = sizeof(si);
    std::wstring exePath = L"D:\\VoskModels\\VoskPy.exe";
    std::wstring workingDir = L"D:\\VoskModels";
    if (CreateProcessW(exePath.c_str(), NULL, NULL, NULL, FALSE, CREATE_NEW_CONSOLE, NULL, workingDir.c_str(), &si, &piVosk)) {
        SoundStart();
    } else {
        SoundError();
    }
}

void StopVoskProcess() {
    if (piVosk.hProcess != NULL) {
        TerminateProcess(piVosk.hProcess, 0);
        CloseHandle(piVosk.hProcess);
        CloseHandle(piVosk.hThread);
        piVosk = { 0 };
    }
    system("taskkill /F /IM VoskPy.exe /T > nul 2>&1");
    SoundStop();
}

// --- Смена раскладки ---
void ChangeKeyboardLayout() {
    INPUT inputs[4] = {};
    for (int i = 0; i < 4; i++) inputs[i].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = VK_MENU;   
    inputs[1].ki.wVk = VK_LSHIFT; 
    inputs[2].ki.wVk = VK_LSHIFT; 
    inputs[2].ki.dwFlags = KEYEVENTF_KEYUP;
    inputs[3].ki.wVk = VK_MENU;   
    inputs[3].ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(4, inputs, sizeof(INPUT));
}

// --- Буфер обмена ---
void SendKeyCombo(char key) {
    INPUT inputs[4] = {};
    for (int i = 0; i < 4; i++) inputs[i].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = VK_CONTROL;
    inputs[1].ki.wVk = (unsigned char)key;
    inputs[2].ki.wVk = (unsigned char)key;
    inputs[2].ki.dwFlags = KEYEVENTF_KEYUP;
    inputs[3].ki.wVk = VK_CONTROL;
    inputs[3].ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(4, inputs, sizeof(INPUT));
}

// --- ХУК КЛАВИАТУРЫ (Caps Lock) ---
LRESULT CALLBACK KeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION && wParam == WM_KEYDOWN) {
        KBDLLHOOKSTRUCT* pKeyBoard = (KBDLLHOOKSTRUCT*)lParam;
        if (pKeyBoard->vkCode == VK_CAPITAL) {
            ChangeKeyboardLayout();
            return 1; // Блокируем стандартное переключение Caps Lock
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

// --- ХУК МЫШИ (Боковые кнопки) ---
LRESULT CALLBACK MouseHookProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION) {
        MSLLHOOKSTRUCT* pMouseStruct = (MSLLHOOKSTRUCT*)lParam;
        
        if (wParam == WM_XBUTTONDOWN || wParam == WM_XBUTTONUP || 
            wParam == WM_NCXBUTTONDOWN || wParam == WM_NCXBUTTONUP) {
            
            WORD xButton = HIWORD(pMouseStruct->mouseData);

            if (xButton == XBUTTON1 || xButton == XBUTTON2) {
                if (wParam == WM_XBUTTONDOWN || wParam == WM_NCXBUTTONDOWN) {
                    bool ctrlPressed = (GetAsyncKeyState(VK_CONTROL) & 0x8000);
                    
                    if (xButton == XBUTTON2) { // Верхняя
                        if (ctrlPressed) SendKeyCombo('C');
                        else StartVoskProcess();
                    } 
                    else if (xButton == XBUTTON1) { // Нижняя
                        if (ctrlPressed) SendKeyCombo('V');
                        else StopVoskProcess();
                    }
                }
                return 1; // Мертвая блокировка системных функций
            }
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

int main() {
    // 1. Проверка на запущенную копию
    HANDLE hMutex = CreateMutexA(NULL, TRUE, "VoskControl_Unique_Mutex_777");
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        SoundError(); 
        if (hMutex) CloseHandle(hMutex);
        return 1; 
    }

    // 2. Установка хуков
    HHOOK hMouseHook = SetWindowsHookEx(WH_MOUSE_LL, MouseHookProc, GetModuleHandle(NULL), 0);
    HHOOK hKeyHook = SetWindowsHookEx(WH_KEYBOARD_LL, KeyboardProc, GetModuleHandle(NULL), 0);

    if (!hMouseHook || !hKeyHook) {
        SoundError();
        return 1;
    }

    // 3. Цикл сообщений
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    // 4. Очистка
    UnhookWindowsHookEx(hMouseHook);
    UnhookWindowsHookEx(hKeyHook);
    if (hMutex) {
        ReleaseMutex(hMutex);
        CloseHandle(hMutex);
    }
    
    return 0;
}