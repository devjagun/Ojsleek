with Ada.Text_IO;           use Ada.Text_IO;
with Ada.Integer_Text_IO;   use Ada.Integer_Text_IO;
with Ada.Float_Text_IO;     use Ada.Float_Text_IO;
with Ada.Strings.Unbounded; use Ada.Strings.Unbounded;
with Ada.Strings.Fixed;     use Ada.Strings.Fixed;

procedure Rebate_Calc is

   type Calculation_Input is record
      Customer_ID        : Integer;
      Total_Units        : Integer;
      Base_Revenue       : Float;
      Certification_Days : Integer;
      Is_Specialty_Cert  : Integer;
      Customer_Class     : Integer;
   end record;

   function Calculate_Volume_Index(Units : Integer) return Float is
   begin
      if Units < 10000 then
         return 0.95;
      elsif Units < 25000 then
         return 1.00;
      elsif Units < 50000 then
         return 1.05;
      elsif Units < 100000 then
         return 1.10;
      else
         return 1.15;
      end if;
   end Calculate_Volume_Index;

   function Calculate_Product_Mix_Factor(
      Is_Spec_Cert : Integer;
      Cert_Days    : Integer;
      Units        : Integer
   ) return Float is
      Factor           : Float := 1.00;
      Has_Spec_Cert    : Boolean;
      Qualifies_Cert   : Boolean;
      Is_High_Volume   : Boolean;
   begin
      Has_Spec_Cert  := (Is_Spec_Cert = 1);
      Is_High_Volume := (Units > 50000);
      Qualifies_Cert := (Cert_Days >= 180);

      if Has_Spec_Cert and Qualifies_Cert then
         Factor := Factor + 0.18;
      end if;

      if Is_High_Volume then
         Factor := Factor + 0.12;
      end if;

      Factor := Float(Integer(Factor * 100.0 + 0.5)) / 100.0;
      return Factor;
   end Calculate_Product_Mix_Factor;

   function Calculate_Customer_Class_Rate(Customer_Class : Integer) return Float is
   begin
      case Customer_Class is
         when 1 => return 0.020;
         when 2 => return 0.025;
         when 3 => return 0.030;
         when 4 => return 0.040;
         when 5 => return 0.050;
         when others => return 0.020;
      end case;
   end Calculate_Customer_Class_Rate;

   Input        : Calculation_Input;
   Vol_Index    : Float;
   Mix_Factor   : Float;
   Class_Rate   : Float;
   Total_Rebate : Float;
   Line         : String(1..512);
   Last         : Natural;
   Pos          : Natural;
   Start        : Natural;
   Field        : Natural := 1;

begin
   Get_Line(Line, Last);

   Pos := 1;
   Start := 1;

   while Pos <= Last and Field <= 6 loop
      if Line(Pos) = ' ' or Pos = Last then
         declare
            Field_Str : constant String :=
               (if Pos = Last then Line(Start..Pos) else Line(Start..Pos-1));
            Trimmed   : constant String := Trim(Field_Str, Ada.Strings.Both);
         begin
            case Field is
               when 1 => Input.Customer_ID := Integer'Value(Trimmed);
               when 2 => Input.Total_Units := Integer'Value(Trimmed);
               when 3 => Input.Base_Revenue := Float'Value(Trimmed);
               when 4 => Input.Certification_Days := Integer'Value(Trimmed);
               when 5 => Input.Is_Specialty_Cert := Integer'Value(Trimmed);
               when 6 => Input.Customer_Class := Integer'Value(Trimmed);
               when others => null;
            end case;
         end;
         Field := Field + 1;
         Start := Pos + 1;
      end if;
      Pos := Pos + 1;
   end loop;

   Vol_Index  := Calculate_Volume_Index(Input.Total_Units);
   Mix_Factor := Calculate_Product_Mix_Factor(
      Input.Is_Specialty_Cert,
      Input.Certification_Days,
      Input.Total_Units
   );
   Class_Rate := Calculate_Customer_Class_Rate(Input.Customer_Class);

   Total_Rebate := Input.Base_Revenue * Vol_Index * Mix_Factor * Class_Rate;
   Total_Rebate := Float(Integer(Total_Rebate * 100.0 + 0.5)) / 100.0;

   Put(Input.Customer_ID, Width => 1);
   Put(" ");
   Put(Vol_Index, Fore => 1, Aft => 2, Exp => 0);
   Put(" ");
   Put(Mix_Factor, Fore => 1, Aft => 2, Exp => 0);
   Put(" ");
   Put(Class_Rate, Fore => 1, Aft => 3, Exp => 0);
   Put(" ");
   Put(Total_Rebate, Fore => 1, Aft => 2, Exp => 0);
   New_Line;

end Rebate_Calc;
