program TB_TR;
var r: real; a,b: integer;
begin
  r := 2.7;
  a := trunc(r);
  b := round(r);
  writeln(a, ' ', b);
end.
