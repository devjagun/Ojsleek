import subprocess
import os

def get_workspace_path():
    if os.path.exists("/workspace/bonus_engine"):
        return "/workspace"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(script_dir), "environment")

WORKSPACE = get_workspace_path()
FORTRAN_PATH = os.path.join(WORKSPACE, "bonus_engine", "bonus_calc.f90")

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def fix_fortran_code():
    content = read_file(FORTRAN_PATH)
    
    content = content.replace(
        "if (zd >= 30) then",
        "if (zd > 30) then"
    )
    
    old_function = '''    function gr(tr, s, ty) result(v)
        character(*), intent(in) :: tr
        real(8), intent(in) :: s
        integer, intent(in) :: ty
        real(8) :: v
        
        if (trim(tr) == 'Gold') then
            v = 1.15d0
        else if (s > 150.0d0) then
            v = 1.10d0
        else if (trim(tr) == 'Gold' .and. s > 150.0d0) then
            v = 1.25d0
        else if (ty > 2) then
            v = 1.05d0
        else
            v = 1.00d0
        end if
        
    end function gr'''
    
    new_function = '''    function gr(tr, s, ty) result(v)
        character(*), intent(in) :: tr
        real(8), intent(in) :: s
        integer, intent(in) :: ty
        real(8) :: v
        
        if (trim(tr) == 'Gold' .and. s > 150.0d0) then
            v = 1.25d0
        else if (trim(tr) == 'Gold') then
            v = 1.15d0
        else if (s > 150.0d0) then
            v = 1.10d0
        else if (ty > 2) then
            v = 1.05d0
        else
            v = 1.00d0
        end if
        
    end function gr'''
    
    content = content.replace(old_function, new_function)
    
    write_file(FORTRAN_PATH, content)

def rebuild_service():
    os.chdir(WORKSPACE)
    subprocess.run(
        ["docker", "compose", "build", "bonus-calc"],
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["docker", "compose", "up", "-d", "bonus-calc"],
        check=True,
        capture_output=True
    )

def main():
    fix_fortran_code()
    rebuild_service()

if __name__ == "__main__":
    main()
